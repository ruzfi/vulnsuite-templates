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
The probes show that the debugger's interactive console is reachable, not just
that a traceback is rendered (that is what the scanner matches on `/`):

| request | vulnerable (debug on) | patched (debug off) |
| --- | --- | --- |
| `GET /console` | 200, the Werkzeug console page with `CONSOLE_MODE = true` … `EVALEX = true` (code evaluation enabled, behind the PIN) | 404, Werkzeug's `The requested URL was not found on the server`, no `EVALEX` |
| `GET /?__debugger__=yes&cmd=resource&f=debugger.js` | 200 JavaScript, the debugger's own client (`createInteractiveConsole`) served by the debug middleware | 500, the plain `The server encountered an internal error` page (the query reaches the app route, which raises) |

Both patched assertions are positive (Werkzeug's own 404 / 500 bodies). No code
is ever evaluated: the console stays PIN-locked and the probes only read pages
the middleware serves to anyone.

## Detection
`nuclei:flask-werkzeug-debug` fires on the vulnerable state and stays silent on
the patched one (2026-11-21).

<!-- No CVE facts, severity, or version boundaries here — see contract.yaml metadata. -->
