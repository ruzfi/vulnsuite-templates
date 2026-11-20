port ENV.fetch("PORT", 3000)
workers ENV.fetch("WEB_CONCURRENCY", 2).to_i
threads 3, 3
stdout_redirect "/rails/log/puma.log", "/rails/log/puma.log", true
