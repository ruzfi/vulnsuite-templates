import os, glob, time, socket, signal, struct, json, http.client
LOG = "/var/log/asan"
def workers():
    out = []
    for d in glob.glob("/proc/[0-9]*"):
        try:
            cmd = open(d + "/cmdline", "rb").read()
        except OSError:
            continue
        if cmd.startswith(b"nginx: worker"):
            out.append(int(d[6:]))
    return out
def wait_worker(t=10):
    end = time.time() + t
    while time.time() < end:
        w = workers()
        if w: return w
        time.sleep(0.05)
    raise SystemExit("no worker")
def state(pid):
    try: return open("/proc/%d/stat" % pid).read().rsplit(")", 1)[1].split()[0]
    except OSError: return "?"
class Docker:
    def __init__(s, path="/var/run/docker.sock"): s.path = path
    def post(s, url):
        c = socket.socket(socket.AF_UNIX); c.connect(s.path)
        c.sendall(("POST %s HTTP/1.0\r\nHost: d\r\nContent-Length: 0\r\n\r\n" % url).encode())
        r = c.recv(4096); c.close(); return r.split(b"\r\n")[0]
def freeze(method, ctr="uaf98-ngx"):
    if method == "sigstop":
        ws = workers()
        for p in ws: os.kill(p, signal.SIGSTOP)
        end = time.time() + 2
        while time.time() < end and any(state(p) != "T" for p in ws): time.sleep(0.001)
        return ws
    if method == "pause":
        Docker().post("/containers/%s/pause" % ctr); return None
def thaw(method, ws, ctr="uaf98-ngx"):
    if method == "sigstop":
        for p in ws: os.kill(p, signal.SIGCONT)
    elif method == "pause":
        Docker().post("/containers/%s/unpause" % ctr)
def proc_net(pid, f):
    rows = []
    for l in open("/proc/%d/net/%s" % (pid, f)).read().splitlines()[1:]:
        p = l.split()
        lp = int(p[1].split(":")[1], 16); rp = int(p[2].split(":")[1], 16)
        rx = int(p[4].split(":")[1], 16); tx = int(p[4].split(":")[0], 16)
        rows.append(dict(lport=lp, rport=rp, st=p[3], rx=rx, tx=tx))
    return rows
def wait_until(fn, t=2.0):
    end = time.time() + t
    while time.time() < end:
        if fn(): return True
        time.sleep(0.002)
    return False
def rst(sock):
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0)); sock.close()
def asan_files(): return set(glob.glob(LOG + "/asan.*"))
def errlog_size():
    try: return os.path.getsize(LOG + "/error.log")
    except OSError: return 0
def errlog_since(off):
    with open(LOG + "/error.log", errors="replace") as f:
        f.seek(off); return f.read()
