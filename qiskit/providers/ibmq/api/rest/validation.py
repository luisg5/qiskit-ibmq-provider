# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2019, 2020.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Schemas for validation."""
# TODO The schemas defined here should be merged with others under rest/schemas
# when they are ready
import time

from marshmallow import pre_load
from marshmallow.validate import OneOf

from qiskit.providers.ibmq.apiconstants import ApiJobStatus
from qiskit.assembler.disassemble import disassemble
from qiskit.validation import BaseSchema, BaseModel, bind_schema
from qiskit.validation.fields import String, Nested, Integer, DateTime, Float, Url

from qiskit.providers.ibmq.utils.fields import map_field_names
from qiskit.providers.ibmq.api.exceptions import UserTimeoutExceededError


# Helper schemas.

class InfoQueueResponseSchema(BaseSchema):
    """Queue information schema, nested in StatusResponseSchema"""

    # Optional properties
    position = Integer(required=False, missing=None)
    _status = String(required=False, missing=None)
    estimated_start_time = DateTime(required=False, missing=None)
    estimated_complete_time = DateTime(required=False, missing=None)
    hub_priority = Float(required=False, missing=None)
    group_priority = Float(required=False, missing=None)
    project_priority = Float(required=False, missing=None)

    @pre_load
    def preprocess_field_names(self, data, **_):  # type: ignore
        """Pre-process the info queue response fields."""
        FIELDS_MAP = {  # pylint: disable=invalid-name
            'status': '_status',
            'estimatedStartTime': 'estimated_start_time',
            'estimatedCompleteTime': 'estimated_complete_time',
            'hubPriority': 'hub_priority',
            'groupPriority': 'group_priority',
            'projectPriority': 'project_priority'
        }
        return map_field_names(FIELDS_MAP, data)


# Endpoint schemas.

class StatusResponseSchema(BaseSchema):
    """Schema for StatusResponse"""

    # Optional properties
    infoQueue = Nested(InfoQueueResponseSchema, required=False)

    # Required properties
    status = String(required=True, validate=OneOf([status.value for status in ApiJobStatus]))


class BackendJobLimitResponseSchema(BaseSchema):
    """Schema for BackendJobLimit"""

    # Optional properties
    maximum_jobs = Integer(required=True)
    running_jobs = Integer(required=True)

    @pre_load
    def preprocess_field_names(self, data, **_):  # type: ignore
        """Pre-process the jobs limit response fields."""
        FIELDS_MAP = {  # pylint: disable=invalid-name
            'maximumJobs': 'maximum_jobs',
            'runningJobs': 'running_jobs'
        }
        return map_field_names(FIELDS_MAP, data)


class TranspilerServiceResponseSchema(BaseSchema):
    """Schema for transpiler service"""
    # Required properties.
    # TODO: Could change these fields to Url type when in place
    upload_url = String(required=True, description="the object storage upload url to use for transpilation.")
    download_url = String(required=True, description="the object storage download url to use for transpilation.")


@bind_schema(TranspilerServiceResponseSchema)
class IBMQTranspilerService(BaseModel):
    """Transpiler Service

    # TODO: Update docs.
    Returns:
        pass
    """
    def __init__(self, api: 'AccountClient', upload_url: str, download_url, **kwargs):
        self.upload_url = upload_url
        self.download_url = download_url
        self._api = api
        super().__init__(**kwargs)

    def run(self, qobj, transpile_config: dict = None, wait: int = 3, timeout: int = None):
        """Submit the payload to the upload url.

        # Update doc.
        Returns:
            pass
        """
        # Make a request to upload the job via url
        qobj_dict = qobj.to_dict()
        # Update the configuration if it is passed.
        if transpile_config:
            qobj_dict['transpile_config'] = transpile_config
        # Still need to update the configuration with the qobj.
        _ = self._api.transpiler_service_submit(self.upload_url, qobj_dict)

        # Poll for the result.
        start_time = time.time()
        serverless_transpiler_response = None
        while serverless_transpiler_response is None:
            elapsed_time = time.time() - start_time
            if timeout is not None and elapsed_time >= timeout:
                raise UserTimeoutExceededError('Timeout while waiting circuit trasnpilation {}')
            time.sleep(wait)
            try:
                serverless_transpiler_response = self._api.transpiler_service_result(self.download_url)
            except Exception as ex:  # TODO: What would be a worthy exception to keep going?
                pass

        circuits, _, _ = disassemble(serverless_transpiler_response)
        return circuits[0] if len(circuits) == 1 else circuits
