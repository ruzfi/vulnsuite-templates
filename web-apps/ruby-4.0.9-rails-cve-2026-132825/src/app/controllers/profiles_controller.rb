class ProfilesController < ApplicationController
  skip_forgery_protection

  def show
    render plain: "profile: guest\n"
  end

  def update
    render plain: "profile updated: #{params[:name].to_s.truncate(40)}\n"
  end
end
