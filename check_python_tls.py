from urllib.request import urlopen

x = urlopen('https://www.howsmyssl.com/a/check').read()
y = x.decode("utf-8")

print(y)
