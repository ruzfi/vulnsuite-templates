#!/bin/sh
# usage: run_resolver.sh <image-tag> <variant> <method> <n>
set -e
H=$(cd "$(dirname "$0")" && pwd)
IMG=uaf98-ngx:$1; V=$2; M=$3; N=$4
docker rm -f uaf98-ngx uaf98-dns >/dev/null 2>&1 || true
docker volume rm uaf98-logs >/dev/null 2>&1 || true
docker network create uaf98 >/dev/null 2>&1 || true
docker run -d --name uaf98-dns --network uaf98 --network-alias dns -v "$H":/h:ro python:3.12-alpine python -u /h/fakedns.py >/dev/null
sleep 1
docker run -d --name uaf98-ngx --network uaf98 --network-alias ngx -v uaf98-logs:/var/log/asan \
  -v "$H/${CONF:-nginx-resolver.conf}":/etc/nginx/nginx.conf:ro $IMG >/dev/null
sleep 1
docker run --rm --network uaf98 --pid container:uaf98-ngx -v uaf98-logs:/var/log/asan -v "$H":/h:ro -v "$H/out":/out -w /h \
  -v /var/run/docker.sock:/var/run/docker.sock python:3.12-alpine python -u /h/${DRIVER:-resolver_driver.py} "$V" "$M" "$N"
docker rm -f uaf98-ngx uaf98-dns >/dev/null
