#!/bin/sh
# usage: run_mail.sh <image-tag> <variant> <method> <n>
H=$(cd "$(dirname "$0")" && pwd)
IMG=uaf98-ngx:$1; V=$2; M=$3; N=$4
docker rm -f uaf98-ngx uaf98-auth >/dev/null 2>&1 || true
docker volume rm uaf98-logs >/dev/null 2>&1 || true
docker network create uaf98 >/dev/null 2>&1 || true
docker run -d --name uaf98-auth --network uaf98 --network-alias auth -v "$H":/h:ro python:3.12-alpine python -u /h/authstub.py >/dev/null
sleep 1
docker run -d --name uaf98-ngx --network uaf98 --network-alias ngx -v uaf98-logs:/var/log/asan \
  -v "$H/${CONF:-nginx-mail.conf}":/etc/nginx/nginx.conf:ro $IMG >/dev/null
sleep 1
docker run --rm --network uaf98 --pid container:uaf98-ngx -v uaf98-logs:/var/log/asan -v "$H":/h:ro -v "$H/out":/out -w /h \
  -v /var/run/docker.sock:/var/run/docker.sock python:3.12-alpine python -u /h/mail_driver.py "$V" "$M" "$N"
docker rm -f uaf98-ngx uaf98-auth >/dev/null
