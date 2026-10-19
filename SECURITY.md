# Security policy

`vulnsuite-templates` is a catalog of **deliberately vulnerable** target
definitions for [vulnsuite](https://github.com/ruzfi/vulnsuite). The targets are
*meant* to be exploitable -- that is the point, not a bug.

## What is and isn't a vulnerability here

**Out of scope -- please do not report these:**

- The CVE or weakness a target reproduces (for example the path traversal in
  `apache-httpd-2.4.49-cve-2021-41773`). Targets are vulnerable on purpose.
- A target being reachable after you deliberately exposed it. Run targets only
  on isolated networks you control -- see "Safe use" below.

**In scope -- please do report these:**

- A template that can affect the **host** beyond the container it stands up:
  escaping the build/run sandbox, reading or writing host files, or executing
  code on the host. The engine's trust model is documented in
  [vulnsuite/SECURITY.md](https://github.com/ruzfi/vulnsuite/blob/main/SECURITY.md).
- A contributed template that ships a **working, weaponized exploit** instead of
  a detection / reachability / version check, or that points `base` at an image
  or source doing more than standing up the affected service (supply-chain abuse).
- Problems in this repo's **CI / workflows** (secret exposure, command injection).

## Reporting

Report in-scope issues **privately**, not as a public issue:

- Preferred: GitHub **"Report a vulnerability"** (this repo's *Security* tab ->
  Private vulnerability reporting).
- Or email the maintainer: riyan@ruz.fi

Include the template id (or workflow), the host-affecting behaviour, and how to
reproduce it. We aim to acknowledge within a few days.

## Safe use

These targets stand up real, exploitable software -- including releases affected
by actively-exploited CVEs. Run them **only** on networks you own, keep the
default `internal` exposure (nothing is published on the host), and never leave
a target reachable from the Internet. See the README's *Safety* section.
