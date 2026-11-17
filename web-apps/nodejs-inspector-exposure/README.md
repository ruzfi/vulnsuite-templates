# nodejs-inspector-exposure

> Config-axis target: the same image in both states, differing only by whether
> the process is launched with the V8 inspector exposed.

## Design
The vulnerable state's `command` starts Node with `--inspect=0.0.0.0:9229`; the
patched state is the default launch (no inspector). The app port (3000) is the
primary port and the readiness check; the inspector lives on a **secondary**
port, 9229.

## Verification
- Vulnerable: an HTTP probe with a per-probe port override reads
  `/json/version` on 9229, which returns the V8 inspector metadata. No debugger
  is attached.
- Patched: a `tcp` probe asserts port 9229 is closed.

## Detection
`custom-only`: no upstream nuclei template discriminates this.

<!-- No CVE facts, severity, or version boundaries here — see contract.yaml metadata. -->
