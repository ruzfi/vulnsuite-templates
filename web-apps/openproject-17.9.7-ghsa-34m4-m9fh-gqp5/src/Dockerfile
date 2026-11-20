FROM openproject/openproject:17.9.7-slim@sha256:4e978557b4009dfdcdab6f18acd1aa9348a2c41ce5cd50c3d535e4c093a5c505
USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends nginx \
 && rm -rf /var/lib/apt/lists/*
COPY vulnsuite/nginx.conf /etc/nginx/vulnsuite.conf
COPY vulnsuite/start vulnsuite/verify-ruby2shell /usr/local/bin/
RUN chmod 0755 /usr/local/bin/start /usr/local/bin/verify-ruby2shell
USER app
EXPOSE 8080
ENTRYPOINT ["./docker/prod/entrypoint-slim.sh"]
CMD ["/usr/local/bin/start"]
