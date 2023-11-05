

import cmd
import getpass
import logging

from cli.blobservice import BlobService, AuthService

_COMMENT_TAG_ = '#'


class Shell(cmd.Cmd):
    """CMD shell implementation"""
    prompt = ''
    stop_on_error = True
    bad_exit = False
    interactive = True
    line_no = 0
    error_cause = 'Unknown error, see logs'
    _auth_ = None
    _blob_ = None

    @property
    def interrupted(self):
        if self.stop_on_error:
            self.bad_exit = True
            return True
        return None

    @property
    def auth_client(self):
        return self._auth_

    @auth_client.setter
    def auth_client(self, new_client: AuthService):
        self._auth_ = new_client
        self.__select_prompt__()

    @property
    def blob_client(self):
        return self._blob_

    @blob_client.setter
    def blob_client(self, new_client: BlobService):
        self._blob_ = new_client
        self.__select_prompt__()

    def output(self, out: str):
        logging.debug(out)
        print(out)

    def preloop(self) -> None:
        self.__select_prompt__()
        return super().preloop()

    def precmd(self, line: str) -> str:
        self.line_no += 1
        self.__select_prompt__()
        cleanLine = line.strip()
        if cleanLine.startswith(_COMMENT_TAG_):
            return ""
        return super().precmd(line)

    def postcmd(self, stop: bool, line: str) -> bool:
        self.__select_prompt__()
        return super().postcmd(stop, line)

    def __select_prompt__(self):
        self.prompt = ''
        if self.interactive:
            self.prompt = 'Blob Rest'
            if self.auth_client is not None:
                if self.auth_client.user is not None and self.auth_client.logged:
                    self.prompt += f'({self.auth_client.user})'
                else:
                    self.prompt += '(offline)'
            self.prompt += ': '

    def default(self, line: str) -> bool:
        self.output(f'*** Unknown syntax: {line}')
        return self.stop_on_error

    def do_get_blobs(self, line):
        """Get the list of blobs"""
        if not self.blob_client:
            logging.error('No connected to a Blob service, connect first')
            return self.stop_on_error
        try:
            blobs = self.blob_client.getBlobs()
            for blob in blobs:
                print(blob)
        except Exception as error:
            logging.error(f'Cannot get blobs: {error}')
            return self.stop_on_error

    def do_get_blob(self, line):
        """Get the blob"""
        if not self.blob_client:
            logging.error('No connected to a Blob service, connect first')
            return self.stop_on_error
        line = line.strip().split()
        if len(line) != 1:
            logging.error('get_blob takes one argument only')
            return self.stop_on_error
        blob_id = line[0]
        try:
            blob = self.blob_client.getBlob(blob_id)
            print(blob.blobId)
        except Exception as error:
            logging.error(f'Cannot get blob: {error}')
            return self.stop_on_error

    def do_delete_blob(self, line):
        """Delete the blob"""
        if not self.blob_client:
            logging.error('No connected to a Blob service, connect first')
            return self.stop_on_error
        line = line.strip().split()
        if len(line) != 1:
            logging.error('delete_blob takes one argument only')
            return self.stop_on_error
        blob_id = line[0]
        try:
            self.blob_client.deleteBlob(blob_id)
        except Exception as error:
            logging.error(f'Cannot delete blob: {error}')
            return self.stop_on_error

    def do_create_blob(self, line):
        """Create a blob"""
        if not self.blob_client:
            logging.error('No connected to a Blob service, connect first')
            return self.stop_on_error
        line = line.strip().split()
        if len(line) != 1:
            logging.error('create_blob takes one argument only')
            return self.stop_on_error
        path = line[0]
        try:
            blob = self.blob_client.createBlob(path)
            print(blob.blobId)
        except Exception as error:
            logging.error(f'Cannot create blob: {error}')
            return self.stop_on_error

    def do_connect_to_auth(self, auth_url):
        """Set the auth service URI"""
        if self.auth_client is None:
            logging.debug('Setting client Auth Url to: ', auth_url)
            self.auth_client = AuthService(auth_url)
            return
        self.output(f'*** AuthService already connected. disconnect first!')
        return self.stop_on_error

    def do_connect_to_blob(self, blob_url):
        """Set the blob service URI"""
        if self.blob_client is None:
            logging.debug('Setting client Blob Url to: ', blob_url)
            self.blob_client = BlobService(blob_url)
            return
        self.output(f'*** BlobService already connected. disconnect first!')
        return self.stop_on_error

    def do_disconnect(self, line):
        """Unset the service URI"""
        if self.blob_client is None:
            self.output('*** BlobService already disconnected, connect first!')
            return self.stop_on_error
        if self.auth_client is None:
            self.output('*** AuthService already disconnected, connect first!')
            return self.stop_on_error
        logging.debug('Unsetting client URL')
        if self.auth_client.logged:
            self.auth_client.logout()
        self.auth_client = None
        self.blob_client = None

    def do_login(self, line):
        """Get a user token"""
        if not self.auth_client:
            logging.error('No connected to an Auth service, connect first')
            return self.stop_on_error
        if self.auth_client.logged:
            logging.error('Already logged, logout first')
            return self.stop_on_error
        line = line.strip().split()
        if len(line) == 0:
            username = prompt_string('Enter username: ')
            password = prompt_password(confirm_password=False)
        elif len(line) == 1:
            username = line[0]
            password = prompt_password(confirm_password=False)
        elif len(line) == 2:
            username, password = line
        else:
            logging.error('new_user takes two optional argumens only')
            return self.stop_on_error
        try:
            self.auth_client.login(username, password)
        except Exception as error:
            logging.error(f'Cannot create new user: {error}')
            return self.stop_on_error

    def do_logout(self, line):
        """Logout client instance"""
        if not self.auth_client:
            logging.error('No connected to an Auth service, connect first')
            return self.stop_on_error
        if not self.auth_client.logged:
            logging.error('Already logged out, login first')
            return self.stop_on_error
        try:
            self.auth_client.logout()
        except Exception as error:
            logging.error(f'Cannot logout: {error}')
            return self.stop_on_error

    def do_EOF(self, line):
        """Disconnect and quit"""
        return self.do_quit(line)

    def do_quit(self, line):
        """Disconnect and quit"""
        if self.auth_client is not None:
            if self.auth_client.logged:
                self.auth_client.logout()
        return True

    def help_get_blobs(self):
        self.output("""Usage:
\tget_blobs
Get the list of blobs""")

    def help_get_blob(self):
        self.output("""Usage:
\tget_blob <BLOB_ID>
Get the blob""")

    def help_delete_blob(self):
        self.output("""Usage:
\tdelete_blob <BLOB_ID>
Delete the blob""")

    def help_create_blob(self):
        self.output("""Usage:
\tcreate_blob <PATH>
Create a blob""")
    def help_connect_to_auth(self):
        self.output("""Usage:
\tconnect_to_auth <AUTH_uri>
Instance new Auth client with the given URL.""")

    def help_connect_to_blob(self):
        self.output("""Usage:
\tconnect_to_blob <BLOB_uri>
Instance new Blob client with the given URL.""")

    def help_disconnect(self):
        self.output("""Usage:
\tdisconnect
Delete current client instance.""")

    def help_quit(self):
        self.output("""Usage:
\tquit
Disconnects and close the shell.""")


def prompt_string(message) -> str:
    """Ask user for something"""
    try:
        return input(message)
    except KeyboardInterrupt as error:
        logging.error('User cancel interactive prompt')
        raise error


def prompt_password(confirm_password=True) -> str:
    """Ask user for a password"""
    while True:
        try:
            password = getpass.getpass()
            if not confirm_password:
                return password
            repeat_password = getpass.getpass('Repeat password: ')
        except KeyboardInterrupt as error:
            logging.error('User cancel interactive prompt')
            raise error
        if password == repeat_password:
            return password
        logging.error('Passwords does not match!')
