description "softhddevice frontend"
author "Marco Scholl <yavdr@marco-scholl.de>"

kill timeout 15
nice -10

respawn
respawn limit 10 5

env HOME=/var/lib/vdr

umask 0000
chdir /var/lib/vdr

