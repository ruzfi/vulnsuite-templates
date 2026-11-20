Rails.application.routes.draw do
  root "pages#home"
  get "up" => "rails/health#show", as: :rails_health_check
  resource :profile, only: [:show, :update]
end
