# nodejs-inspector-exposure

> Config-axis target: the same image in both states, differing only by whether
> the process is launched with the V8 inspector exposed.

## Design
The vulnerable state's `command` starts Node with `--inspect=0.0.0.0:9229`; the
patched state is the default launch (no inspector). The app port (3000) is the
primary port and the readiness check; the inspector lives on a **secondary**
port, 9229, declared with `publish: true` so `-expose host` publishes it too
(otherwise neither a scanner nor the verify probe can reach it from the host).

## Verification
- Vulnerable: an HTTP probe with a per-probe port override reads
  `/json/version` on 9229, which returns the inspector metadata
  (`"Browser": "node.js/v…"`; Node 18 does not include `V8-Version`). No
  debugger is attached.
- Patched: an `exec` probe connects to 127.0.0.1:9229 from inside the container
  and asserts the connection is refused. A host-side `tcp closed` probe cannot
  be used: in `-expose host` mode Docker's port proxy accepts connections on a
  published port even when nothing listens behind it.

## Detection
`custom-only`: no upstream nuclei template discriminates this.

<!-- No CVE facts, severity, or version boundaries here — see contract.yaml metadata. -->
