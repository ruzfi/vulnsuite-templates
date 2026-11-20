require_relative "boot"

require "rails"
require "action_controller/railtie"
require "action_view/railtie"

Bundler.require(*Rails.groups)

module Ruby2shellLab
  class Application < Rails::Application
    config.load_defaults 8.1
    config.eager_load = true
    config.consider_all_requests_local = false
    config.secret_key_base = ENV.fetch("SECRET_KEY_BASE")
    config.logger = ActiveSupport::TaggedLogging.logger($stdout)
    config.log_tags = [:request_id]
  end
end
