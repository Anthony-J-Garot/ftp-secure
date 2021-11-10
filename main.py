import os
import re

import ssl
import ftplib  # For FTP and FTP_TLS
import pysftp  # For SFTP
from paramiko import transport
import subprocess

# FTP
FTP_SERVER = "ftp.us.debian.org"
# FTP_TLS
FTP_TLS_SERVER = "ftpserver"
FTP_TLS_PORT = 21
SELF_SIGNED_CERTIFICATE = 'ssl/pure-ftpd.pem'
# SFTP
SFTP_SERVER = "localhost"
EXTRA_KNOWN_HOSTS = 'extra_known_hosts'  # in addition to the ~/.ssh/known_hosts
SSH_PRIVATE_KEY = '~/.ssh/id_rsa'
SFTP_PORT = 2222
# Misc
UPLOAD_DIR = 'upload'
FILE_NAME = 'SAMPLE.txt'  # A file that exists in ./upload dir
DOWNLOAD_DIR = 'download'
USERNAME = 'anthony'
PASSWORD = 'pass'


class MyFTP_TLS(ftplib.FTP_TLS):
    """
Explicit FTPS, with shared TLS session.
This was necessary to get the prot_p option to work, i.e. the data protection level
set to private, which means data is also encrypted using TLS.
    """

    def ntransfercmd(self, cmd, rest=None):
        conn, size = ftplib.FTP.ntransfercmd(self, cmd, rest)
        if self._prot_p:
            session = self.sock.session
            if isinstance(self.sock, ssl.SSLSocket):
                session = self.sock.session
            conn = self.context.wrap_socket(conn,
                                            server_hostname=self.host,
                                            session=session)  # this is the fix
        return conn, size


def ftp_get_file(file_name, remote_dir=None, local_dir=None):
    """
Connects to an FTP server and tries to pull a file, by name, using binary mode.
This is the simplest scenario, so, at present, this assumes an anonymous connection.
NOTE: At present I don't have a container running vanilla ftp.
    """

    # Into where files are downloaded
    if local_dir is not None:
        print(f"Changing local dir to {local_dir}")
        os.chdir(local_dir)

    # https://docs.python.org/3/library/ftplib.html
    ftp = ftplib.FTP(FTP_SERVER)
    ftp.login(user='anonymous', passwd='', acct='')

    if remote_dir is not None:
        print(f"Changing remote dir to {remote_dir}")
        ftp.cwd(remote_dir)

    # Not strictly necessary, but it's nice to see what's there
    ftp.retrlines('LIST')

    # Open a binary file for write. This will hold the contents of what SFTP pulls in.
    with open(file_name, 'wb') as fp:
        ftp.retrbinary(f'RETR {file_name}', fp.write)

    ftp.close()


def ftp_tls_get_file(file_name, remote_dir=None, local_dir=None):
    """
Connects to an FTP server, using TLS, and tries to pull a file, by name, using binary mode.
The self-signed certificate is generated when the server starts through one or more of
the ENV variables.
    """

    USE_SELF_SIGNED = True
    if USE_SELF_SIGNED:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = True
        context.verify_mode = ssl.VerifyMode.CERT_REQUIRED
        context.load_verify_locations(SELF_SIGNED_CERTIFICATE)
    else:
        # This works, but it's probably not the safest
        context = ssl.create_default_context()

    # Into where files are downloaded
    if local_dir is not None:
        print(f"Changing local dir to {local_dir}")
        os.chdir(local_dir)

    # https://docs.python.org/3/library/ftplib.html
    ftp_tls = MyFTP_TLS(host=FTP_TLS_SERVER, context=context)
    ftp_tls.set_debuglevel(1)
    ftp_tls.connect(port=FTP_TLS_PORT, timeout=10)
    ftp_tls.login(user=USERNAME, passwd=PASSWORD, acct='')

    print(f"Sock is {ftp_tls.sock}")

    ftp_tls.set_pasv(True)
    # Switch to secure data connection.
    # IMPORTANT! Otherwise, only the user and password is encrypted and not all the file data.
    ftp_tls.prot_p()
    ftp_tls.pwd()

    if remote_dir is not None:
        print(f"Changing remote dir to {remote_dir}")
        ftp_tls.cwd(remote_dir)

    # Not strictly necessary, but it's nice to see what's there
    ftp_tls.retrlines('LIST')
    ftp_tls.mlsd()

    # Open a binary file for write. This will hold the contents of what SFTP pulls in.
    with open(file_name, 'wb') as fp:
        ftp_tls.retrbinary(f'RETR {file_name}', fp.write)

    ftp_tls.close()


def sftp_get_file(file_name, remote_dir=None, local_dir=None):
    """
Connects to an SFTP server and tries to pull a file, by name, using binary mode.
    """

    print("Preferred keys")
    print(transport.Transport._preferred_keys)
    print()

    # The following cnopts settings are useful for debugging, but can give man in the middle issue,
    # so it isn't the preferred way to specify the host keys. Instead, create an EXTRA_KNOWN_HOSTS
    # file. See below.
    # cnopts = pysftp.CnOpts()
    # cnopts.hostkeys = None

    # pysftp does not support the host key entries with the port.
    create_extra_known_hosts()

    # The ~/.ssh/known_hosts file entries cannot be read directly, so pull the
    # value from ~/.ssh/known_hosts then clean off the cruft to the first space.
    # e.g
    #   localhost ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIP/wejs5idhfLwnNlzLOCskSrMYkgoMC8+Tsnx/yg+lu
    cnopts = pysftp.CnOpts(knownhosts=EXTRA_KNOWN_HOSTS)

    # https://pysftp.readthedocs.io/en/release_0.2.9/cookbook.html
    with pysftp.Connection(
            host=SFTP_SERVER,
            private_key=SSH_PRIVATE_KEY,
            username=USERNAME,
            password=PASSWORD,
            port=SFTP_PORT,
            cnopts=cnopts) as sftp:

        # Into where files are downloaded
        if local_dir is not None:
            print(f"Changing local dir to {local_dir}")
            os.chdir(local_dir)

        if remote_dir is not None:
            print(f"Changing remote dir to {remote_dir}")
            sftp.cwd(remote_dir)

        # Not strictly necessary, but it's nice to see what's there
        print(f"PWD: {sftp.pwd}")
        print(f"LS: {sftp.listdir()}")

        # Open a binary file for write. This will hold the contents of what SFTP pulls in.
        print(f"About to get file {file_name}")
        sftp.get(file_name)

        print("Closing SFTP connection")
        sftp.close()

def create_extra_known_hosts():
    """
pysftp does not support the host key entries with the port.
https://stackoverflow.com/questions/64438184/pysftp-throwing-paramiko-ssh-exception-sshexception-even-though-known-hosts-file
So we gotta do some footwork.
    """
    SSH_KEYSCAN = '/usr/bin/ssh-keyscan'
    output = subprocess.run([SSH_KEYSCAN, "-p", str(SFTP_PORT), SFTP_SERVER], capture_output=True)

    pattern = re.compile('^\[(.+)\]:\d+$')
    if output.returncode == 0:
        with open(EXTRA_KNOWN_HOSTS, "w") as out:
            lines = output.stdout.decode('utf-8').split('\n')
            for line in lines:
                # print(f"CHECKING {line}\n")
                pieces = line.split(' ')
                # print (f"PIECES {pieces[0]}\n")
                match = pattern.match(pieces[0])
                if match:
                    # print(match[1])
                    pieces[0] = match[1]
                    out.write(" ".join(pieces))

if __name__ == '__main__':
    # Clean existing file that might have been pulled from before
    if os.path.exists(f"{DOWNLOAD_DIR}/{FILE_NAME}"):
        os.remove(f"{DOWNLOAD_DIR}/{FILE_NAME}")

    sftp_get_file(
        file_name=FILE_NAME,
        remote_dir=UPLOAD_DIR
    )

    ftp_tls_get_file(
        file_name=FILE_NAME,
        remote_dir=UPLOAD_DIR,
        local_dir=DOWNLOAD_DIR
    )
