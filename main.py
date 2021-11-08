import os
import ssl
from ftplib import FTP, FTP_TLS
import pysftp  # For SFTP

# FTP
FTP_SERVER = "ftp.us.debian.org"
# FTP_TLS
FTP_TLS_SERVER = "ftpserver"
FTP_TLS_PORT = 21
# SFTP
SFTP_SERVER = "localhost"
EXTRA_KNOWN_HOSTS = 'extra_known_hosts'  # in addition to the ~/.ssh/known_hosts
SSH_PRIVATE_KEY = '~/.ssh/id_rsa'
SFTP_PORT = 2222
SFTP_USER = 'anthony'
SFTP_PASSWORD = 'pass'
# File name that exists in upload dir
UPLOAD_DIR = 'upload'
FILE_NAME = 'SAMPLE.txt'
DOWNLOAD_DIR = 'download'


def ftp_get_file(file_name, directory_name=None):
    """
Connects to an FTP server and tries to pull a file, by name, using binary mode.
This is the simplest scenario, so, at present, this assumes an anonymous connection.
    """

    # https://docs.python.org/3/library/ftplib.html
    ftp = FTP(FTP_SERVER)
    ftp.login(user='anonymous', passwd='', acct='')
    if directory_name is not None:
        ftp.cwd(directory_name)

    # Not strictly necessary, but it's nice to see what's there
    ftp.retrlines('LIST')

    # Open a binary file for write. This will hold the contents of what SFTP pulls in.
    with open(file_name, 'wb') as fp:
        ftp.retrbinary(f'RETR {file_name}', fp.write)

    ftp.quit()


def ftp_tls_get_file(file_name, directory_name=None):
    """
Connects to an FTP server, using TLS, and tries to pull a file, by name, using binary mode.
    """

    USE_SELF_SIGNED = True
    if USE_SELF_SIGNED:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = True
        context.verify_mode = ssl.VerifyMode.CERT_REQUIRED
        context.load_verify_locations('/usr/share/ca-certificates/pure-ftpd.crt')
    else:
        # This works, but it's probably not the safest
        context = ssl.create_default_context()

    # https://docs.python.org/3/library/ftplib.html
    ftp_tls = FTP_TLS(host=FTP_TLS_SERVER, context=context)
    ftp_tls.set_debuglevel(1)
    ftp_tls.connect(port=21, timeout=10)
    ftp_tls.login(user='anthony', passwd='pass', acct='Normal')

    print(f"Sock is {ftp_tls.sock}")

    ftp_tls.set_pasv(True)
    # Switch to secure data connection.
    # IMPORTANT! Otherwise, only the user and password is encrypted and not all the file data.
    ftp_tls.prot_p()
    # ftp_tls.ccc()
    ftp_tls.pwd()

    if directory_name is not None:
        ftp_tls.cwd(directory_name)

    # Not strictly necessary, but it's nice to see what's there
    ftp_tls.retrlines('LIST')
    ftp_tls.mlsd()

    # Open a binary file for write. This will hold the contents of what SFTP pulls in.
    with open(file_name, 'wb') as fp:
        ftp_tls.retrbinary(f'RETR {file_name}', fp.write)

    ftp_tls.close()


def sftp_get_file(file_name, directory_name=None):
    """
Connects to an SFTP server and tries to pull a file, by name, using binary mode.
    """

    # This is useful for debugging, but can give man in the middle issue,
    # so it isn't the preferred way to specify the host keys. Instead,
    # create an EXTRA_KNOWN_HOSTS file. See below.
    # cnopts = pysftp.CnOpts()
    # cnopts.hostkeys = None

    # The ~/.ssh/known_hosts file entries cannot be read directly, so pull the
    # value from ~/.ssh/known_hosts then clean off the cruft to the first space.
    # e.g
    #   localhost ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIP/wejs5idhfLwnNlzLOCskSrMYkgoMC8+Tsnx/yg+lu
    cnopts = pysftp.CnOpts(knownhosts=EXTRA_KNOWN_HOSTS)

    # https://pysftp.readthedocs.io/en/release_0.2.9/cookbook.html
    with pysftp.Connection(
            host=SFTP_SERVER,
            private_key=SSH_PRIVATE_KEY,
            username=SFTP_USER,
            password=SFTP_PASSWORD,
            port=SFTP_PORT,
            cnopts=cnopts) as sftp:
        if directory_name is not None:
            print(f"Changing remote dir to {directory_name}")
            sftp.cwd(directory_name)

        # Not strictly necessary, but it's nice to see what's there
        print(f"PWD: {sftp.pwd}")
        print(f"LS: {sftp.listdir()}")

        # Open a binary file for write. This will hold the contents of what SFTP pulls in.
        print(f"About to get file {file_name}")
        sftp.get(file_name)

        print("Closing SFTP connection")
        sftp.close()


if __name__ == '__main__':
    # Clean existing file that might have been pulled from before
    if os.path.exists(f"{DOWNLOAD_DIR}/{FILE_NAME}"):
        os.remove(f"{DOWNLOAD_DIR}/{FILE_NAME}")

    # Change to the download directory before starting the FTP server.
    # Anything we download will go into here.
    os.chdir(DOWNLOAD_DIR)

    # sftp_get_file(
    #     file_name=FILE_NAME,
    #     directory_name=UPLOAD_DIR
    # )

    ftp_tls_get_file(
        file_name=FILE_NAME,
        directory_name=UPLOAD_DIR
    )
