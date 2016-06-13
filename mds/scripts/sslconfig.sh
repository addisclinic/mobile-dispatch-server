#!/bin/bash
DIR='/var/cache/ssl'
mkdir -p ${DIR}
openssl genrsa -des3 -out ${DIR}/server.key 2048
openssl rsa -in ${DIR}/server.key -out ${DIR}/server.key.insecure
mv ${DIR}/server.key ${DIR}/server.key.secure
mv ${DIR}/server.key.insecure ${DIR}/server.key
openssl req -new -key ${DIR}/server.key -out ${DIR}/server.csr
openssl x509 -req -days 1875 -in ${DIR}/server.csr -signkey ${DIR}/server.key -out ${DIR}/server.crt
mv ${DIR}/server.crt /etc/ssl/certs
mv ${DIR}/server.key /etc/ssl/private
rm -rf ${DIR}
