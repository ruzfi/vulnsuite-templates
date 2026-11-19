# Issue #98 — first experiment: freeze/resume + probe-controlled sidecars on the nginx race UAFs


Setup: nginx `140aa942711868a8daeb95810bc9a81f272ada72` (release-1.31.8), the ASan Dockerfile from the issue comment
(`-O1 -fsanitize=address -DNGX_DEBUG_PALLOC=1`), OrbStack linux/arm64, `worker_processes 1`.
Images: `vuln` (stock), `fix-resolver` (+`e39708edc69a`), `fix-mail` (+`754fe68c2e0f`), plus a `vuln-debug`
(`--with-debug`) used only for diagnosis. Patch presence was checked in each image.
A hit is an ASan `heap-use-after-free` report in the new writable log dir whose stack contains `ngx_resolver` (resolver CVE) or `ngx_mail` (mail CVE). Every hit also made the worker exit (`exited with code 1`, because `halt_on_error=1`).

## TL;DR

| CVE | Best variant | vulnerable | patched |
| --- | --- | --- | --- |
| CVE-2026-123634 resolver | freeze (SIGSTOP worker) + held DNS + request-ordering precondition | **60/60** | **0/60** |
| CVE-2026-123634 resolver | same, `docker pause` instead of SIGSTOP | **60/60** | **0/60** |
| CVE-2026-113425 mail | freeze (SIGSTOP worker) + write-event precondition | **58/60** (2 = harness errors, 58/58 of valid attempts) | **0/60** |
| CVE-2026-113425 mail | same, `docker pause` | **57/60** (3 = harness errors, 57/57 valid) | **0/60** |

**Both race UAFs verify deterministically with freeze/resume. Freeze alone did not do it, though.** Each CVE also needs a protocol-level precondition that the prototype in #98 lacked. Without the precondition, freeze gives **0/60** for both. That, not timing jitter, is why the prototype saw 0/180 and only "benign `send() failed`".

1. Resolver: the main request's resolve context must come **before** the mirror subrequest's in `rn->waiting`. Getting that order takes a split request body.
2. Mail: nginx's **client write event must already be armed in epoll** (from an earlier EAGAIN on the client socket). Getting that state takes reply backpressure.

## Setup fix: ASan log dir

The known gap is real. With `log_path=/var/log/nginx/asan`, a process running as `nginx` prints
`ERROR: Can't open file: /var/log/nginx/asan.22 (reason: 13)`, and the report never reaches a file.
The fix used here is `install -d -m 1777 /var/log/asan` plus `log_path=/var/log/asan/asan`. A deliberately UAF-ing ASan binary run as `nginx` then wrote `asan.<pid>` there, and all real hits below landed there too. The dir was a named volume shared with the checker container.

## CVE-2026-123634 (resolver, e39708edc69a)

### Mechanism (from the code, confirmed by the ASan stacks)

`ngx_resolver_process_a()` detaches the waiter list (`next = rn->waiting; rn->waiting = NULL`). It then sets
`ctx->state = code` per ctx and calls `ctx->handler(ctx)`, reading `next = ctx->next` first.
If handler(ctx_main) terminates the main request, the termination runs every cleanup, including the mirror subrequest's upstream cleanup. That calls `ngx_resolve_name_done(ctx_mirror)`. ctx_mirror still has `state == NGX_AGAIN` but is no longer in `rn->waiting`, so it logs `[alert] could not cancel ... resolving` and **frees** the ctx. The loop then writes `ctx->state` into freed memory at `ngx_resolver.c:2142`.

Sample stack (`harness/out/sample-freeze-split-dnsfirst-sigstop.txt`):
`WRITE ... ngx_resolver_process_a ngx_resolver.c:2142`. Freed by `ngx_resolve_name_done` ←
`ngx_http_upstream_cleanup` ← `ngx_http_terminate_request` ← `ngx_http_finalize_request` ←
`ngx_http_upstream_finalize_request` ← `ngx_http_upstream_resolve_handler:1271`.

So three conditions must all hold:

1. **ctx_main must be ahead of ctx_mirror in the waiting list.** New waiters are *prepended*. In the normal flow the main request resolves first, the mirror subrequest runs from posted requests and resolves second, and the list is `[mirror, main]`. Then the mirror's handler runs first, and no UAF is possible. To get `[main, mirror]`, use `mirror_request_body off` and send the request body in two parts. The mirror resolves while the main request is still waiting for its body, and the main request resolves only after the last body byte arrives.
2. **handler(ctx_main) must terminate the request synchronously.** An NXDOMAIN answer leads to `finalize(502)`. That writes the 502 to the client, the write fails with ECONNRESET, `c->error` is set, and the request is terminated.
3. **The client RST must be in the socket but not yet processed when the DNS event runs.** If the client's EPOLLRDHUP event is handled first, `ngx_http_upstream_check_broken_connection` finalizes the request and both ctxs are cancelled cleanly. epoll's ready list is FIFO, so the DNS answer must become ready *before* the RST arrives, and both must be in one `epoll_wait` batch.

### Config (`harness/nginx-resolver.conf`)

```nginx
resolver dns:53 ipv6=off valid=1s;
location /  { mirror /m; mirror_request_body off; proxy_pass http://$arg_h; }
location = /m { internal; proxy_pass http://$arg_h; }
```

`$arg_h` is a unique name per attempt, so the resolver cache never answers.

### Sidecars

- `harness/fakedns.py`: holds every UDP query. Its TCP control port `:5300` accepts `WAIT <name> <t>`, `RELEASE nx|a:<ip>` and `FLUSH`.
- Driver container (`harness/resolver_driver.py`, `python:3.12-alpine`): on the same network, with `--pid container:<nginx>` (for SIGSTOP and `/proc/<worker>/net/*`) and the docker socket (for the `pause` variant).

### Trigger sequence that works (100%)

```
1. connect nginx:80; send "POST /?h=<uniq> HTTP/1.1 ... Content-Length: 2\r\n\r\nA"   (1 of 2 body bytes)
2. dns: WAIT <uniq>          -> mirror subrequest's query is held
3. send "B"; sleep 50ms      -> main request resolves too (joins the same node, no new query)
4. FREEZE worker             (SIGSTOP worker PIDs, or docker pause)
5. dns: RELEASE nx           ; wait until worker's UDP socket rx_queue > 0   (/proc/<w>/net/udp)
6. client: SO_LINGER{1,0}; close  -> RST ; wait until the conn leaves /proc/<w>/net/tcp
7. RESUME                    -> one epoll_wait returns [udp, client]; UDP first -> UAF
8. check /var/log/asan/asan.* for heap-use-after-free + ngx_resolver
```

### Results (N=60 each)

| variant | vulnerable | patched |
| --- | --- | --- |
| a. no split, no freeze (DNS release then immediate RST; ≈ prototype) | 0/60 | 0/60 |
| a'. split body, no freeze (release then immediate RST) | **33/60 (55%)** | 0/60 |
| b0. no split, freeze, DNS-then-RST | 0/60 | 0/60 |
| **b. split, freeze (SIGSTOP), DNS-then-RST** | **60/60** | **0/60** |
| c. split, freeze (SIGSTOP), RST-then-DNS | 0/60 | 0/60 |
| b'. split, freeze (`docker pause`), DNS-then-RST | **60/60** | **0/60** |

Every vulnerable hit also logged `[alert] could not cancel <name> resolving` and a worker exit.

**Patched positive control:** on `fix-resolver`, variant b logs `writev() failed (104: Connection reset by peer) while sending to client` after `could not be resolved (3: Host not found)`. That is the same racy path, taken inside the resolve handler, and it neither crashes nor raises an alert. The 0/60 is therefore a real negative, not a missed race.
Variant c logs `epoll_wait() reported that client prematurely closed connection` instead, which confirms the ordering argument.

Side effect of SIGSTOP/SIGCONT: one harmless `[info] epoll_wait() failed (4: Interrupted system call)` per attempt.

## CVE-2026-113425 (mail auth_http, 754fe68c2e0f)

### Mechanism

On `PASS`, the POP3 auth state handler leaves its default reply (`+OK`) in `s->out` and calls `ngx_mail_auth()` → `ngx_mail_auth_http_init()`, which does not send it. `ngx_mail_send` stays the client write handler. If the client write event fires in that same loop pass and the send fails, `ngx_mail_close_connection()` destroys the session pool. The auth_http peer connection still has `data = s`, and its connect-complete write handler then reads freed `s`. Sample stack (`harness/out/sample-mail-freeze-prime-sigstop.txt`):
`READ ... ngx_mail_auth_http_write_handler ngx_mail_auth_http_module.c:247`, freed by
`ngx_destroy_pool` ← `ngx_mail_close_connection` ← `ngx_mail_send:813` ← `ngx_epoll_process_events`.

**Why freeze alone gives 0.** On epoll, nginx registers only the **read** event for a mail connection (`ev:80002001`). The write event is added (`op:3 ev:80002005`) only after a `send()` returns EAGAIN. On RST, `ngx_epoll_process_events` turns EPOLLERR/HUP into EPOLLIN|EPOLLOUT, but it only calls the write handler `if (wev->active)`. With the write event not armed, the stale `+OK` is never sent and the session survives. The `send() failed ... while in auth state` lines the prototype saw are the **benign** error reply sent after `Auth-Wait`, once auth has completed. The debug log confirms this: `client login failed: "Invalid login"` comes first.

**The open question from the issue (unread data + RST, read after resume).** On this Linux kernel, recv() **does return data queued before the RST**. In 60/60 freeze attempts without priming, nginx parsed `PASS` and issued the auth_http request (`held=60`), even though the RST was already in the socket when the worker resumed. So "data + RST in the same tick" is reachable. It just isn't sufficient.

### Precondition: arm the client write event (client-side only, no config change)

The client uses a small `SO_RCVBUF` (2048) and sends `CAPA\r\n` one at a time without reading the replies. It stops when nginx stops reading its input: the server socket's rx_queue stays above 0 for 30 ms (`/proc/<w>/net/tcp`), which means `s->out` is blocked on EAGAIN. That took about 565 commands. The client then drains all replies and syncs on one invalid command (`-ERR`). Pipelining must stay under nginx's **128-byte POP3 command buffer**, or nginx answers "client sent too long command" and resets. That is the source of the 2–3 harness errors per 60 below.

### Trigger sequence that works (100% of valid attempts)

```
1. connect :110 (SO_RCVBUF=2048); read banner; prime write event (above); sync
2. USER u -> +OK
3. FREEZE worker (SIGSTOP or docker pause)
4. send "PASS p\r\n"; wait until worker socket rx_queue > 0
5. RST (SO_LINGER 0); wait until conn leaves /proc/<w>/net/tcp
6. RESUME -> read handler parses PASS, starts auth_http; write handler sends stale "+OK" -> ECONNRESET
   -> session pool destroyed; auth_http peer write handler (connect done) -> UAF, same loop pass
```

The auth_http stub (`harness/authstub.py`) holds requests. The UAF fires at connect completion, before any response, so for this CVE the stub only needs to *not answer early*. A probe-controlled release is not needed.

### Results (N=60 each)

| variant | vulnerable | patched |
| --- | --- | --- |
| no prime, no freeze (PASS + immediate RST; ≈ prototype) | 0/60 | 0/60 |
| prime, no freeze (PASS + immediate RST) | 10/60 (17%) | 0/60 |
| prime, no freeze, 1 ms between PASS and RST | 2/60 | 0/60 |
| no prime, freeze (SIGSTOP) | 0/60 | 0/60 |
| **prime, freeze (SIGSTOP)** | **58/60** (2 priming errors; 58/58 valid) | **0/60** |
| **prime, freeze (`docker pause`)** | **57/60** (3 priming errors; 57/57 valid) | **0/60** |

**Patched positive control:** on `fix-mail`, prime+freeze issued the auth_http request in 60/60 attempts and the session survived until the stub's reply. The fix's `s->out.len = 0` makes the write handler a no-op.

`send() failed` is useless as an oracle: it appears in about 58/60 runs of every variant on both builds.

## SIGSTOP vs docker pause (cgroup freezer)

No difference in outcome: 60/60 vs 60/60 for the resolver, 58/58 vs 57/57 valid attempts for mail. Notes:

- `docker pause` on cgroup v2 *is* the cgroup freezer, so a separate cgroup-freezer test would have measured the same mechanism. I did not run one.
- SIGSTOP needs PID matching ("nginx: worker process") and access to the target's PID namespace. After every hit the worker respawns with a new PID, so the PIDs must be matched again before each attempt. It also causes one `EINTR` log line per attempt.
- `docker pause` freezes everything in the container, including the master and any in-container `exec` client. The trigger must therefore run in another container, which it already did here. It needs only the Docker API, which the core already has.
- In every freeze attempt the kernel delivered UDP, TCP data and RST to the frozen process's sockets (no "not-seen" timeouts). Waiting on `/proc/<pid>/net/{udp,tcp}` worked, but it needs the target's net/PID namespace. I did not test whether a fixed 50–100 ms sleep is enough instead. It probably is, because delivery on the bridge takes microseconds.

## Implications for the core design in #98

| Proposal | Needed? | Evidence |
| --- | --- | --- |
| 1. freeze/resume step | **Yes.** It takes 55%→100% (resolver) and 17%→100% (mail). | tables above |
| 2. probe-controlled sidecars / exec-in-sidecar | **Exec-in-sidecar: yes. Control-port convention: no.** The trigger has to run in a container on the target network (`docker pause` freezes in-container exec). It needs raw-socket control that http/tcp/net probes lack: a split body, an RST via `SO_LINGER 0`, a small rcvbuf, backpressure. The resolver also needs a DNS sidecar that holds answers. The driver script can drive that over the private network itself, so the core only needs "run this command in sidecar X". | harness |
| 3. sanitizer oracle, core-owned writable log dir | **Yes.** The gap is confirmed (EACCES, report lost). The core should mount a dir with mode 1777 into the target and read it after the step. Attribution needs a frame regex (`ngx_resolver`/`ngx_mail`), not just the bug class. | sanity test |
| 3b. worker-crash counter | **Useful but secondary.** With `halt_on_error=1` the master logs `exited with code 1`, **not** "exited on signal", so match both. It is cheap, but it says nothing about stock (non-ASan) builds, which I did not measure. | logs |
| 4. `fidelity: instrumented` (race-widening patch) | **Not needed.** No source change beyond the fix. Both states run identical code apart from the upstream fix. | – |
| 5. `attempts` / `min_hits` | **Not needed for correctness.** It is still worth having for harness flakiness: mail priming failed 2–5% of the time. `attempts: 3, min_hits: 1` on vulnerable and `0 hits` required on patched would absorb that. | mail table |

Additional things the core design should account for:

- **Freeze has to wrap actions taken *during* the freeze, not just "a request".** The ordering inside the frozen window decides the outcome: resolver DNS-then-RST gives 60/60, RST-then-DNS gives 0/60. `release_after: trigger` works if one sidecar command does everything between freeze and resume. A cleaner shape is explicit `freeze` / `resume` steps around sidecar exec steps.
- **The resolver also needs setup *before* the freeze**: a partial body, waiting for the held query, the rest of the body. So verify needs to be an ordered **sequence of steps** that share one client connection. In practice the whole client lives in one driver script that the core signals, or the driver does the freeze itself via a core-provided hook. Simplest version: the core exposes freeze/resume to the driver sidecar, for example as an env var with a control endpoint or a mounted docker-API proxy limited to pause/unpause of the target.
- **Each target needs a positive control on patched.** Here it was "same racy log line, no ASan". Otherwise a 0/N on patched may just mean the race was never reached. A per-state `expect_log` alongside `expect_sanitizer: none` would express that.

### Minimal YAML shape this experiment supports

```yaml
service:
  sidecars:
    - { name: dns,    image: ..., digest: ..., command: ["python", "/fakedns.py"] }
    - { name: driver, image: ..., digest: ..., command: ["sleep", "infinity"] }
  sanitizer:
    log_dir: /var/log/asan          # core mounts a 1777 volume here; target sets ASAN_OPTIONS log_path into it
verify:
  - sequence:
      attempts: 3                   # harness flake budget, not probability
      min_hits: 1                   # vulnerable; patched requires 0 of attempts
      steps:
        - exec: { container: driver, run: "/trigger.py setup" }   # partial body, wait for held DNS query, rest of body
        - freeze: { target: container }                           # docker pause (or process: "nginx: worker process")
        - exec: { container: driver, run: "/trigger.py fire" }    # release DNS, wait, RST
        - resume: {}
        - expect_sanitizer: { kind: heap-use-after-free, frame: "ngx_resolver_process_a" }
    patched:
      expect_sanitizer: none
      expect_log: "writev\\(\\) failed .* while sending to client"   # positive control: race reached
```

The mail target has the same shape: setup = prime write event, then USER; fire = PASS then RST. The auth sidecar is a plain stub.

## Negative results and caveats

- Freeze without the protocol precondition: **0/60 for both CVEs**. A generic "freeze + request + reset" feature will not verify these by itself; the target author has to know the precondition.
- The resolver variant with an A answer pointing at a closed port was not tested. NXDOMAIN gives the synchronous finalize path most directly.
- HTTP/2 (`2df48a501d0f`) and HTTP/3 (`b5252dae1ca0`) were not attempted.
- Single host (OrbStack arm64, one worker). Hit rates without freeze (55%, 17%) depend on scheduling and will vary by machine. The freeze results should not.
- Stock (non-ASan) builds were not measured, so it is unknown whether a crash counter alone would see these UAFs.

## Files

- `Dockerfile` (ASan build, `PATCHES` build-arg, `/var/log/asan` 1777), `Dockerfile.debug`
- `harness/fakedns.py`, `harness/authstub.py`: holding sidecars with a TCP control port
- `harness/common.py`, `harness/resolver_driver.py`, `harness/mail_driver.py`: drivers (freeze via SIGSTOP or the docker API)
- `harness/run_resolver.sh`, `harness/run_mail.sh`, `harness/matrix_*.sh`: orchestration
- `harness/out/matrix-*.txt`, `harness/out/{res,mail}-*.log`: per-attempt results
- `harness/out/sample-*.txt`: full ASan reports
