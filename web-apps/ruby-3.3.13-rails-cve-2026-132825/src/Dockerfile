FROM ruby:3.3.13-slim@sha256:db3ad6dd68a886d51a187fb9bf486052f2976cdbe3b750169c25092aba1297fa

ENV RAILS_ENV=production \
    BUNDLE_DEPLOYMENT=1 \
    BUNDLE_WITHOUT=development:test \
    SECRET_KEY_BASE=ruby2shell-lab-not-a-secret \
    HTTP_PORT=80 \
    TARGET_PORT=3000

WORKDIR /rails
RUN apt-get update -qq \
 && apt-get install -y --no-install-recommends build-essential \
 && rm -rf /var/lib/apt/lists/*
COPY Gemfile Gemfile.lock ./
RUN bundle install && rm -rf ~/.bundle "${BUNDLE_PATH}"/ruby/*/cache
COPY . .
RUN mkdir -p log tmp && chown -R 1000:1000 log tmp \
 && useradd --uid 1000 --create-home rails
USER 1000:1000
EXPOSE 80
CMD ["/rails/bin/start"]
