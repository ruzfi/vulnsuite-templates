#!/bin/sh
set -e
# FPM_STATUS (per state) is the single toggle between the vulnerable and secure
# configurations. The default FPM pool (www.conf) has no pm.status_path, so
# /status is unavailable; enabling it is the misconfiguration.
if [ "$FPM_STATUS" = "1" ]; then
  echo 'pm.status_path = /status' >> /usr/local/etc/php-fpm.d/www.conf
fi
php-fpm -D
exec nginx -g 'daemon off;'
