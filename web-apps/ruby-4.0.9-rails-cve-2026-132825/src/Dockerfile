FROM ruby:4.0.9-slim@sha256:d8cb2c0714bdaba0f318af897a01d2dbde3cfa8e62d47e99cea55feb13c0e90d

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
