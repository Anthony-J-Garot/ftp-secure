# Introduction

This was a pilot project to see what SFTP might look like.
That was fairly straightforward. Then I was curious what 
TLS over FTP might look like.

SFTP is preferred over TLS over FTP because it uses only one port.

## Dockerfile(s)

Initially I had this project set up with a single docker-compose.yml
file, but while trying to debug an issue with PureFTP, I wanted
some tools inside the container, e.g. VIM and ps. I understand
that some folks want the bare minimum in their docker containers,
but not adding procps? Really?

## SFTP notes

- https://github.com/atmoz/sftp
- https://hub.docker.com/r/atmoz/sftp/dockerfile 

Port 22 is normally for SSH but is also used for SFTP. 
So, I used 2222 for the localhost port.

## FTP notes

Used PureFTPd.

- https://github.com/stilliard/docker-pure-ftpd
- https://download.pureftpd.org/pub/pure-ftpd/doc/README
- https://docs.python.org/3/library/ftplib.html

## TLS over FTP notes

Got everything working such that a file could be downloaded
from the FTP server using FTP_TLS. However, when `ftp_tls.prot_p()`
was turned on, an error message occurred. Chasing that error
was fruitless.

Eventually loaded lftp:

``` 
$ sudo apt-get install lftp
```

Still unable to do a file LIST, but at least this time the 
error seems more relevant.

```
$ lftp
lftp :~> set ftp:ssl-force true
lftp :~> connect ftpserver
lftp ftpserver:~> login anthony
Password:
lftp anthony@ftpserver:~> ls
ls: Fatal error: Certificate verification: Not trusted (19:CE:F2:E3:D3:AB:A4:95:53:5D:84:64:71:3A:5E:DB:E6:2F:EF:74)
lftp anthony@ftpserver:~> set ssl:verify-certificate no
lftp anthony@ftpserver:~> ls
drwxrwxrwx    2 1000       1000             4096 Nov  4 14:39 upload
```

It would seem that not verifying the self-signed certificate
is necessary in the python code.

### Using a self-signed certificate

On the client machine, which is Linux:
$ sudo apt-get install ca-certificates

Then TTY into the container:

```
./d6.sh tty 1
cd /etc/ssl/private
cat pure-ftpd.pem
```

Copy the BEGIN CERTIFICATE to END CERTIFICATE stuff.

Back on the client Linux box:

```
$ sudo vim /usr/share/ca-certificates/pure-ftpd.crt
```

Paste what you copied.

```
$ sudo dpkg-reconfigure ca-certificates
```

Obviously choose the pure-ftpd.crt.

# Where To Begin With This Project

Build both images and start them using the d6.sh script:
```
./d6.sh build
```

Now you can run the python script.

```
python3 main.py
```

# d6.sh Tool

This is a tool that simplifies certain docker procedures, 
e.g. build, rm, rmi, and other docker functions on the 
specific images.

(The name comes from the number of letters inside the word
"docker." I have a k10.sh script when working w/ kubernetes.)

There are two images in this project. These are both added
into the bash array. The index number can then be used to 
specify an action on a particular image (or container based
upon that image).

For example, consider a scenario in which the container built
from the `ftp_secure_ftp_tls` image is giving issues. You make
various changes to the docker-compose file to rememedy the 
situation. A progression of debugging might look something 
like this:

```
# Make a change to docker-compose.yml
vim docker-compose.yml

# Stop and remove the container associated with the 
# ftp_secure_ftp_tls image. Then remove the image itself.
./d6.sh rmi 1

# Stop the container associated with ftp_secure_sftp image
# (because d6.sh wants all related containers stopped).
./d6.sh stop 0

# Build uses the docker-compose.yml to build images that 
# aren't there.
./d6.sh build

# Now tty into the container based upon ftp_secure_ftp_tls
# to see if your change fixed any issues.
./d6.sh tty 1
```


