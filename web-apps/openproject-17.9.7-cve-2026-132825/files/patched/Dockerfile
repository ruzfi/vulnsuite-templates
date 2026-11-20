FROM openproject/openproject:17.9.8-slim@sha256:9555489b1ec84c53275dbf63c4c101e7002222e6f273d7fc10e8ff18f8f726c0
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
