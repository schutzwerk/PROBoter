#!/bin/bash
#**********************************************
#
# Script to generate a self-signed certificate
# for the PROBoter reverse proxy
#
# INTENDED FOR DEVELOPMENT ONLY!!
#
#**********************************************
CERTIFICATE_DIR="./certs"

mkdir -p ${CERTIFICATE_DIR}

openssl ecparam -name secp384r1 -genkey -noout -out ${CERTIFICATE_DIR}/privkey.pem

openssl req -new -x509 \
    -days 365 \
    -key ${CERTIFICATE_DIR}/privkey.pem \
    -out ${CERTIFICATE_DIR}/fullchain.pem -subj "/C=/ST=/L=/O=/CN=proboter.dev"

