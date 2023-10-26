"""API server"""

import sys
import json
import logging
import argparse

from flask import Flask
from server.config import DEFAULT_PORT, DEFAULT_ADDRESS, DEFAULT_STORAGE, DEFAULT_BLOB_DB, HTTPS_DEBUG_MODE


class ApiService:
    '''Wrap all components used by the service'''

    def __init__(self, db_file, admin_token, host=DEFAULT_ADDRESS, port=DEFAULT_PORT):
        self._host_ = host
        self._port_ = port

        self._app_ = Flask(__name__.split('.', maxsplit=1)[0])
        routeApp(self._app_, self._authdb_, self._tokenman_)

        @property
        def base_uri(self):
            '''Get the base URI to access the API'''
            host = '127.0.0.1' if self._host_ in ['0.0.0.0'] else self._host_
            return f'http://{host}:{self._port_}'

        def start(self):
            '''Start HTTP server'''
            self._app_.run(host=self._host_, port=self._port_, debug=HTTPS_DEBUG_MODE)

        def stop(self):
            '''Cancel all remaining timers'''
            self._tokenman_.stop()

    @property
    def base_uri(self):
        '''Get the base URI to access the API'''
        host = '127.0.0.1' if self._host_ in ['0.0.0.0'] else self._host_
        return f'http://{host}:{self._port_}'

    def start(self):
        '''Start HTTP server'''
        self._app_.run(host=self._host_, port=self._port_, debug=HTTPS_DEBUG_MODE)

    def stop(self):
        '''Cancel all remaining timers'''
        self._tokenman_.stop()


'''
“-p <puerto> o “--port” <puerto>”: establece un puerto de escucha, si no se establece por
defecto será el 3002.

• “-l <dirección>” o “--listening <dirección>”: establece una dirección de escucha, por defecto
se usará “0.0.0.0”.



'''


def parse_commandline():
    """Parse command line"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '-p', '--port', type=int, default=DEFAULT_PORT,
        help='Listening port (default: %(default)s)', dest='port'
    )
    parser.add_argument(
        '-l', '--listening', type=str, default=DEFAULT_ADDRESS,
        help='Listening address (default: all interfaces)', dest='address'
    )
    parser.add_argument(
        '-d', '--db', type=str, default=DEFAULT_BLOB_DB,  # fixme
        help='Database to use (default: %(default)s', dest='db_file'
    )
    parser.add_argument(
        '-s', '--storage', type=str, default=DEFAULT_STORAGE,  # fixme
        help='Database to use (default: %(default)s', dest='storage'
    )
    args = parser.parse_args()
    return args


def main():
    """Entry point for the API"""
    user_options = parse_commandline()

    service = ApiService(
        user_options.db_file, user_options.admin_token, user_options.address, user_options.port
    )
    try:
        print(f'Starting service on: {service.base_uri}')
        service.start()
    except Exception as error:
        logging.error('Cannot start API: %s', error)
        sys.exit(1)

    service.stop()
    sys.exit(0)


if __name__ == '__main__':
    main()
