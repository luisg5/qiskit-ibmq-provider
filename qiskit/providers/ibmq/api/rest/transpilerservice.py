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
        'self': '',
    }

    def __init__(self, session: RetrySession, preset: int) -> None:
        """Job constructor.

        Args:
            session: session to be used in the adaptor.
            job_id: id of the job.
        """
        self.preset = preset
        timestamp = time.time()
        super().__init__(session, '/transpilerService-{}-{}'.format(timestamp, preset))

    def get(self) -> Dict[str, Any]:
        """Return a job.

        Returns:
            json response.
        """
        url = self.get_url('self')
        return self.session.get(url, bare=True).json()
