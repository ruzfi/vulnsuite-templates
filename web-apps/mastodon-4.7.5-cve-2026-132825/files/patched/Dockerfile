FROM ghcr.io/mastodon/mastodon:v4.7.6@sha256:8d46d6d8ac86f16f00a8944e3ba8cd8d1e3de23b33a59354c751e071b58e18a9
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
