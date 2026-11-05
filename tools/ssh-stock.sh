#!/bin/sh
# SSH into the stock HH40V firmware (root / oelinux123). Its dropbear only offers legacy algorithms.
exec ssh -o HostKeyAlgorithms=+ssh-rsa -o PubkeyAcceptedAlgorithms=+ssh-rsa \
	-o KexAlgorithms=+diffie-hellman-group1-sha1 \
	-o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o LogLevel=ERROR \
	root@192.168.1.1 "$@"
