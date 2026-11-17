# flask-werkzeug-debugger

> Config-axis target: the same image in both states, differing only by whether
> the Werkzeug debugger is enabled.

## Design
Not a version bug: the same app is safe or exploitable depending purely on the
Werkzeug debugger. Flask enables it when run with `debug=True` (Django
deployments hit the same thing via django-extensions' `runserver_plus
--werkzeug`). `APP_DEBUG` is set per state so the two are distinct runs of one
build: vulnerable turns the debugger on; patched is the secure default (off).

## Verification
An unhandled error on `/` returns 500 in both states. With the debugger on, the
page is the Werkzeug traceback interpreter; with it off, a plain 500. The
console is never used.

## Detection
`nuclei:flask-werkzeug-debug` is declared from its fingerprint but not yet run
against both states. Set `detection: scanner` once it fires on vulnerable and
stays silent on patched.

<!-- No CVE facts, severity, or version boundaries here — see contract.yaml metadata. -->
