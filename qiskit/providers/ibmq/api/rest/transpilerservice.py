# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2020.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""TranspilerService REST adapter for the IBM Q Experience API."""

import pprint
import time
from json.decoder import JSONDecodeError
from datetime import datetime

from typing import Dict, Any
from marshmallow.exceptions import ValidationError

from .base import RestAdapterBase
from .validation import StatusResponseSchema
from ..session import RetrySession
from ..exceptions import ApiIBMQProtocolError


class TranspilerService(RestAdapterBase):
    """Rest adapter for job related endpoints."""

    URL_MAP = {
        'self': 'https://us-south.functions.cloud.ibm.com/api/v1/web/'
                '1d8ef74d-78f2-4214-a876-b8e011a0c87e/default/object_storage_provider_fn.json',
    }

    def __init__(self, session: RetrySession, preset: int) -> None:
        """Job constructor.

        Args:
            session: session to be used in the adaptor.
            job_id: id of the job.
        """
        self.preset = preset
        self.name = int(time.time())
        super().__init__(session, '')

    def get(self) -> Dict[str, Any]:
        """Return a job.

        Returns:
            json response.
        """
        url = self.get_url('self')
        return self.session.post(url,
                                 json={'name': str(self.name), 'preset': "preset_{}".format(self.preset)},
                                 headers={'Content-Type': 'application/json'},
                                 bare=True).json()
