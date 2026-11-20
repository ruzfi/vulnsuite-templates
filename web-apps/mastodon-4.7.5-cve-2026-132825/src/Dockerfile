FROM ghcr.io/mastodon/mastodon:v4.7.5@sha256:1cf98fb199f8cc1dcf4bb174095656bd5e19e99f29e935c2a838132083e1f609
USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends nginx \
 && rm -rf /var/lib/apt/lists/*
COPY vulnsuite/nginx.conf /etc/nginx/vulnsuite.conf
COPY vulnsuite/start vulnsuite/verify-ruby2shell /usr/local/bin/
RUN chmod 0755 /usr/local/bin/start /usr/local/bin/verify-ruby2shell
USER mastodon
EXPOSE 8080
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/usr/local/bin/start"]
