import os
from flask import Flask

app = Flask(__name__)


@app.route("/healthz")
def healthz():
    # Readiness probe only; never raises, so the healthcheck is stable in both
    # states.
    return "ok", 200


@app.route("/")
def index():
    # Always raises an unhandled error. The response then depends entirely on
    # whether the Werkzeug debugger is enabled: debug on -> interactive
    # traceback page; debug off -> a plain "Internal Server Error".
    raise RuntimeError("vulnsuite demo: unhandled error")


if __name__ == "__main__":
    # APP_DEBUG is set per state (1 = vulnerable, 0 = secure default).
    debug = os.environ.get("APP_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=5000, debug=debug)
