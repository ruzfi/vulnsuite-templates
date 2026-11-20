class PagesController < ApplicationController
  def home
    render html: <<~HTML.html_safe
      <!doctype html>
      <html><head><title>Lab notes</title></head>
      <body><h1>Lab notes</h1>
      <form action="/profile" method="post">
        <input type="hidden" name="_method" value="patch">
        <input name="name" value="guest"><button>Save</button>
      </form></body></html>
    HTML
  end
end
