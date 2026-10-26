# A minimal Flask app whose only variable is whether the Werkzeug interactive
# debugger is enabled (APP_DEBUG, set per state). The debugger is Flask's
# well-known RCE-capable error console; this target proves its exposure benignly
# (the traceback page) without touching the PIN-protected console.
FROM python:3.11-slim
RUN pip install --no-cache-dir "flask==3.0.3" "werkzeug==3.0.3"
WORKDIR /app
COPY app.py .
EXPOSE 5000
CMD ["python", "app.py"]
