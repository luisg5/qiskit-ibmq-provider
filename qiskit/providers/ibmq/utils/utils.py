# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2019.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""General utility functions."""

import os
import re
import logging
import keyword
from typing import List, Optional, Type
from logging import Logger


def to_python_identifier(name: str) -> str:
    """Convert a name to a valid Python identifier.

    Args:
        name: Name to be converted.

    Returns:
        Name that is a valid Python identifier.
    """
    # Python identifiers can only contain alphanumeric characters
    # and underscores and cannot start with a digit.
    pattern = re.compile(r"\W|^(?=\d)", re.ASCII)
    if not name.isidentifier():
        name = re.sub(pattern, '_', name)

    # Convert to snake case
    name = re.sub('((?<=[a-z0-9])[A-Z]|(?!^)(?<!_)[A-Z](?=[a-z]))', r'_\1', name).lower()

    while keyword.iskeyword(name):
        name += '_'

    return name


def validate_job_tags(job_tags: Optional[List[str]], exception: Type[Exception]) -> None:
    """Validates input job tags.

    Args:
        job_tags: Job tags to be validated.
        exception: Exception to raise if the tags are invalid.

    Raises:
        Exception: If the job tags are invalid.
    """
    if job_tags and (not isinstance(job_tags, list) or
                     not all(isinstance(tag, str) for tag in job_tags)):
        raise exception("job_tags needs to be a list or strings.")


def setup_logger(logger: Logger) -> None:
    """Setup the logger for the provider modules with the appropriate level.

    It involves:
        * Use the `QISKIT_IBMQ_PROVIDER_LOG_LEVEL` environment variable to
          determine the log level to use for the provider modules. If an invalid
          level is set, the log level defaults to ``WARNING``. The valid log levels
          are ``DEBUG``, ``INFO``, ``WARNING``, ``ERROR``, and ``CRITICAL``
          (case-insensitive). If the environment variable is not set, then the parent
          logger's level is used, which also defaults to `WARNING`.
        * Use the `QISKIT_IBMQ_PROVIDER_LOG_FILE` environment variable to specify the
          filename to use when logging messages. If a log file is specified, the log
          messages will not be logged to the screen. If a log file is not specified,
          the log messages will only be logged to the screen and not to a file.
    """
    log_level = os.getenv('QISKIT_IBMQ_PROVIDER_LOG_LEVEL', '')
    log_file = os.getenv('QISKIT_IBMQ_PROVIDER_LOG_FILE', '')

    # Setup the formatter for the log messages.
    log_fmt = ('%(name)s.%(module)s.%(funcName)s:%(levelname)s:%(asctime)s:'
               ' %(message)s')
    formatter = logging.Formatter(log_fmt)

    # Set propagate to `False` since handlers are to be attached.
    logger.propagate = False

    # Log messages to a file (if specified), otherwise log to the screen (default).
    if log_file:
        # Setup the file handler.
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    else:
        # Setup the stream handler, for logging to console, with the given format.
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    # Set the logging level after formatting, if specified.
    if log_level:
        # Default to `WARNING` if the specified level is not valid.
        level = logging.getLevelName(log_level.upper())
        if not isinstance(level, int):
            logger.warning('"%s" is not a valid log level. The valid log levels are: '
                           '`DEBUG`, `INFO`, `WARNING`, `ERROR`, and `CRITICAL`.', log_level)
            level = logging.WARNING
        logger.setLevel(level)
