#!/usr/bin/env python3

"""
    Blob Client
"""

import sys
import logging
import argparse
from io import StringIO

from cli.blobservice import BlobService, AuthService
from cli.errors import CMDCLI_ERROR, NO_ERROR, SCRIPT_ERROR
from cli.shell import Shell, prompt_password

_DEB = logging.debug
_ERR = logging.error
_WRN = logging.warning
_INF = logging.info


def main():
    user_options = parse_command_line()

    if not user_options:
        return CMDCLI_ERROR

    exit_code = NO_ERROR

    # Prepare input files
    script_files = []
    if len(user_options.SCRIPTS) == 0:
        _DEB('Enable input commands from standard input')
        script_files.append(sys.stdin)
    else:
        for script_file in user_options.SCRIPTS:
            _DEB(f'Enable commands from file {script_file}')
            script_files.append(open(script_file, 'r'))

    # Use the same client instance for all input files
    blob_client = None
    auth_client = None
    if user_options.BLOBURL is not None and user_options.AUTHURL is not None:
        if user_options.authtoken:
            _DEB('Using Auth token')
            blob_client = BlobService(user_options.BLOBURL, authToken=user_options.authtoken)
            auth_client = AuthService(user_options.AUTHURL, authToken=user_options.authtoken)
        else:
            auth_client = AuthService(user_options.AUTHURL)
            if user_options.username:
                _DEB('Autologin')
                if not user_options.password:
                    user_options.password = prompt_password()
                auth_client.login(user_options.username, user_options.password)
                blob_client = BlobService(user_options.BLOBURL, authToken=auth_client.auth_token)
            else:
                raise Exception('Username is required')

    output = StringIO()
    interactive = False
    raw_input = False
    for input_file in script_files:
        if input_file is sys.stdin:
            raw_input = True
            if sys.stdin.isatty():
                interactive = True
                output = sys.stdout
                stdout_output('Interactive shell initialized')
                stdout_output('Use "?" for help. Ctrl-d to quit.')
        shell = Shell(stdin=input_file, stdout=output)

        shell.auth_client = auth_client
        shell.blob_client = blob_client

        shell.use_rawinput = raw_input
        shell.interactive = interactive
        if user_options.force:
            shell.stop_on_error = False
        shell.output = stdout_output
        shell.cmdloop()
        if shell.bad_exit:
            _ERR('Command process interrupted')
            _ERR(shell.error_cause)
            exit_code = SCRIPT_ERROR
            break

    for fd in script_files:
        if fd is sys.stdin:
            continue
        fd.close()

    return exit_code


def parse_command_line():
    """Parse and check CLI"""
    parser = argparse.ArgumentParser(description='Client for Blob service')

    parser.add_argument('BLOBURL', nargs='?', default=None, help='URL of Blob API.')
    parser.add_argument('AUTHURL', nargs='?', default=None, help='URL of AUTH API.')

    parser.add_argument('SCRIPTS', nargs='*',
                        help='Scripts to run. Stdin (interactive) used if omitted.')

    auth = parser.add_argument_group('Login options')
    auth.add_argument('-a', '--authtoken', default=None,
                      dest='authtoken', help='Set auth token')
    auth.add_argument('-u', '--username', default=None,
                      dest='username', help='Username to auto-login (default: disable auto-login)')
    auth.add_argument('-p', '--password', action='store', default=None,
                      dest='password', help='Set password instead of prompt (not recommended, insecure)')

    running = parser.add_argument_group('Running options')
    running.add_argument('--force', action='store_true', default=False,
                         dest='force', help='Continue even if some error is reported')

    debopts = parser.add_argument_group('Debugging options')
    debopts.add_argument('--debug', '-d', action='store_true', default=False,
                         dest='debug', help='Show debugging messages')

    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)
    return args


def stdout_output(message: str):
    """Message to stdout"""
    if message.strip() != '':
        _DEB(message)
        print(message)


if __name__ == '__main__':
    sys.exit(main())
