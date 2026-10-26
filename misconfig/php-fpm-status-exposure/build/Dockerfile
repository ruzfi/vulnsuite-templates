# Single image bundling nginx + PHP-FPM. The only variable is whether the FPM
# pool exposes its status page (FPM_STATUS, set per state), written into a pool
# config fragment by the entrypoint. PHP-FPM does not expose /status by
# default; enabling pm.status_path is the misconfiguration.
FROM php:8.2-fpm
RUN apt-get update && apt-get install -y --no-install-recommends nginx \
 && rm -rf /var/lib/apt/lists/*
RUN mkdir -p /var/www/html && echo '<?php echo "ok";' > /var/www/html/index.php
COPY default.conf /etc/nginx/conf.d/default.conf
RUN rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
EXPOSE 80
CMD ["/entrypoint.sh"]
