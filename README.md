# Introduction

This was a pilot project to see what SFTP might look like.
That was fairly straightforward. Then I was curious what 
TLS over FTP might look like.

SFTP is preferred over TLS over FTP because it uses only one port.

> Both SFTP and FTP over TLS securely transfer data—usernames, passwords, and file contents. However, SFTP enables bi-directional secure data transfer using one port. FTP over TLS requires multiple ports to be opened on a firewall—one for command data (to establish an encrypted connection) and at least one for file data.

## Dockerfile(s)

Initially this project was set up with a single docker-compose.yml
file, but while trying to debug an issue with PureFTP, tools
were added inside the container(s), e.g. VIM and ps. 

I understand that some folks want the bare minimum for their 
docker containers, but not adding `procps`? Really?

## SFTP notes

Used atmoz/sftp

- [atmoz/sftp Docker Image](https://github.com/atmoz/sftp)
- https://hub.docker.com/r/atmoz/sftp/dockerfile 

Port 22 is normally for SSH but is also used for SFTP. 
So, 2222 is used for the localhost port.

## FTP notes

Used PureFTPd.

- [stilliard/docker-pure-ftpd repo](https://github.com/stilliard/docker-pure-ftpd)
- https://download.pureftpd.org/pub/pure-ftpd/doc/README
- https://docs.python.org/3/library/ftplib.html

## TLS over FTP notes

Got everything working such that a file could be downloaded
from the FTP server using FTP_TLS. However, when `ftp_tls.prot_p()`
was turned on, an error message occurred. Chasing that error
was fruitless.

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

### Debugging

You can change the endpoint to 'tail -f /dev/null' then
run pure-ftpd manually. This dumps the details to the 
console.

Or look in the log file:

```
$ tail -f /var/log/pure-ftpd/pureftpd.log
```

# Where To Begin With This Project

Build both images and start them using the d6.sh script:
```
$ ./d6.sh build
```

A few dependencies and/or useful tools:

``` 
$ sudo apt-get install lftp
$ sudo aptitude install docker-compose
$ pip install pysftp
```

Now you can run the python script.

```
$ python3 main.py

or

$ ipdb3 main.py
```

You can connect using the d6.sh tool:

```
$ ./d6.sh lftp	# For FTP over TLS
$ ./d6.sh sftp	# For sftp
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


