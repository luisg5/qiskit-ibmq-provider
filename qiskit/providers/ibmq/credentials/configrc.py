# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2019.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Utilities for reading and writing credentials from and to configuration files."""

import logging
import os
from ast import literal_eval
from collections import OrderedDict
from configparser import ConfigParser, ParsingError
from typing import Dict, Tuple, Optional, Any

from .credentials import Credentials, HubGroupProject
from .exceptions import InvalidCredentialsFormatError, CredentialsNotFoundError

logger = logging.getLogger(__name__)

DEFAULT_QISKITRC_FILE = os.path.join(os.path.expanduser("~"),
                                     '.qiskit', 'qiskitrc')
"""Default location of the configuration file."""


def read_credentials_from_qiskitrc(
        filename: Optional[str] = None
) -> Dict[HubGroupProject, Credentials]:
    """Read a configuration file and return a dictionary with its contents.

    Args:
        filename: Full path to the configuration file. If ``None``, the default
            location is used (``$HOME/.qiskit/qiskitrc``).

    Returns:
        A dictionary with the contents of the configuration file, in the
        ``{credential_unique_id: Credentials}`` format. The dictionary is
        empty if the input file does not exist.

    Raises:
        InvalidCredentialsFormatError: If the file cannot be parsed. Note
            that this exception is not raised if the input file
            does not exist, and an empty dictionary is returned instead.
    """
    filename = filename or DEFAULT_QISKITRC_FILE
    config_parser = ConfigParser()
    try:
        config_parser.read(filename)
    except ParsingError as ex:
        raise InvalidCredentialsFormatError(
            'Error parsing file {}: {}'.format(filename, str(ex))) from ex

    # Build the credentials dictionary.
    credentials_dict = OrderedDict()  # type: ignore[var-annotated]
    for name in config_parser.sections():
        single_credentials = dict(config_parser.items(name))

        # Individually convert keys to their right types.
        # TODO: consider generalizing, moving to json configuration or a more
        # robust alternative.
        if 'proxies' in single_credentials.keys():
            single_credentials['proxies'] = literal_eval(
                single_credentials['proxies'])
        if 'verify' in single_credentials.keys():
            single_credentials['verify'] = bool(  # type: ignore[assignment]
                single_credentials['verify'])
        if 'default_provider' in single_credentials.keys():
            single_credentials.update(
                _get_default_provider_entry(single_credentials['default_provider']))
            # Delete `default_provider`, since it's not used by the `Credentials` constructor.
            del single_credentials['default_provider']

        new_credentials = Credentials(**single_credentials)  # type: ignore[arg-type]

        credentials_dict[new_credentials.unique_id()] = new_credentials

    return credentials_dict


def _get_default_provider_entry(default_hgp):
    """Return the default hub/group/project to use for a `Credentials` instance.

    TODO: Update docstring.
    Args:
        default_hgp: A string in the form of "<hub_name>/<group_name>/<project_name>",
            read from the configuration file, which indicates the default provider to use
            for a `Credentials` instance.
            TODO: Link this "Credentials" with the place it's defined.

    Returns:
        A dictionary of the form {'hub': <hub_name>, 'group': <group_name>, 'project': <project_name>}.
        If the `default_hgp` is in the correct format, the fields inside the dictionary are given by
        `default_hgp`. Otherwise, the fields in the dictionary will be `None`.
    """
    hgp = default_hgp.split('/')
    if len(hgp) == 3:
        return {'hub': hgp[0], 'group': hgp[1], 'project': hgp[2]}
    else:
        logger.warning('The specified default provider "%s" is invalid. Use the '
                       '"<hub_name>/<group_name>/<project_name>" format to specify '
                       'a default provider. The specified default will not be used.')
        return {'hub': None, 'group': None, 'project': None}


def write_qiskit_rc(
        credentials: Dict[HubGroupProject, Credentials],
        filename: Optional[str] = None
) -> None:
    """Write credentials to the configuration file.

    Args:
        credentials: Dictionary with the credentials, in the
            ``{credentials_unique_id: Credentials}`` format.
        filename: Full path to the configuration file. If ``None``, the default
            location is used (``$HOME/.qiskit/qiskitrc``).
    """
    def _credentials_object_to_dict(credentials_obj: Credentials) -> Dict[str, Any]:
        """Convert a ``Credential`` object to a dictionary."""
        # TODO: Handle the simple keys.
        credentials_dict = {key: getattr(credentials_obj, key)
                            for key in ['token', 'proxies', 'verify']
                            if getattr(credentials_obj, key)}

        # Save the `base_url` in the account, not the hgp `url`.
        if getattr(credentials_obj, 'base_url'):
            credentials_dict['url'] = getattr(credentials_obj, 'base_url')

        # TODO: Handle the default provider.
        hgp_entry = {
            'hub': credentials_obj.hub,
            'group': credentials_obj.group,
            'project': credentials_obj.project
        }

        if all(hgp_entry.values()):
            credentials_dict['default_provider'] = '/'.join(hgp_entry.values())

        return credentials_dict

    def _section_name(credentials_: Credentials) -> str:
        """Return a string suitable for use as a unique section name."""
        base_name = 'ibmq'
        if credentials_.is_ibmq():
            base_name = '{}_{}_{}_{}'.format(base_name,
                                             *credentials_.unique_id())
        return base_name

    filename = filename or DEFAULT_QISKITRC_FILE
    # Create the directories and the file if not found.
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    unrolled_credentials = {
        _section_name(credentials_object):
            _credentials_object_to_dict(credentials_object)
        for _, credentials_object in credentials.items()
    }

    # Write the configuration file.
    with open(filename, 'w') as config_file:
        config_parser = ConfigParser()
        config_parser.read_dict(unrolled_credentials)
        config_parser.write(config_file)


def store_credentials(
        credentials: Credentials,
        overwrite: bool = False,
        filename: Optional[str] = None
) -> None:
    """Store the credentials for a single account in the configuration file.

    Args:
        credentials: Credentials to save.
        overwrite: ``True`` if any existing credentials are to be overwritten.
        filename: Full path to the configuration file. If ``None``, the default
            location is used (``$HOME/.qiskit/qiskitrc``).
    """
    # Read the current providers stored in the configuration file.
    filename = filename or DEFAULT_QISKITRC_FILE
    stored_credentials = read_credentials_from_qiskitrc(filename)

    # Check if duplicated credentials are already stored. By convention,
    # we assume (hub, group, project) is always unique.
    if credentials.unique_id() in stored_credentials and not overwrite:
        logger.warning('Credentials already present. '
                       'Set overwrite=True to overwrite.')
        return

    # Clear `stored_credentials` and write the new credentials to file.
    stored_credentials.clear()
    stored_credentials[credentials.unique_id()] = credentials
    write_qiskit_rc(stored_credentials, filename)


def remove_credentials(
        credentials: Credentials,
        filename: Optional[str] = None
) -> None:
    """Remove credentials from the configuration file.

    Args:
        credentials: Credentials to remove.
        filename: Full path to the configuration file. If ``None``, the default
            location is used (``$HOME/.qiskit/qiskitrc``).

    Raises:
        CredentialsNotFoundError: If there is no account with that name on the
            configuration file.
    """
    # Set the name of the Provider from the class.
    stored_credentials = read_credentials_from_qiskitrc(filename)

    try:
        del stored_credentials[credentials.unique_id()]
    except KeyError:
        raise CredentialsNotFoundError('The account {} does not exist in the configuration file.'
                                       .format(credentials.unique_id())) from None
    write_qiskit_rc(stored_credentials, filename)
