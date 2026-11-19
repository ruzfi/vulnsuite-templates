# auth_http stub that HOLDS every request until released over a TCP control port (:5300).
#   WAIT <n> <timeout> -> "ok" once >= n requests are held
#   RELEASE            -> replies "Auth-Status: Invalid login" to all held, "released N"
import socket, threading, time
held, cv = [], threading.Condition()
def serve(c):
    buf = b""
    while b"\r\n\r\n" not in buf:
        d = c.recv(4096)
        if not d: return
        buf += d
    with cv: held.append(c); cv.notify_all()
def http_loop():
    s = socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", 8080)); s.listen(64)
    while True:
        c, _ = s.accept(); threading.Thread(target=serve, args=(c,), daemon=True).start()
def ctl(c):
    f = c.makefile("rw")
    for line in f:
        p = line.split()
        if p[0] == "WAIT":
            with cv: ok = cv.wait_for(lambda: len(held) >= int(p[1]), timeout=float(p[2]))
            f.write("ok\n" if ok else "timeout\n")
        elif p[0] == "RELEASE":
            with cv: hs = held[:]; held.clear()
            for h in hs:
                try: h.sendall(b"HTTP/1.0 200 OK\r\nAuth-Status: Invalid login\r\nAuth-Wait: 1\r\n\r\n"); h.close()
                except OSError: pass
            f.write("released %d\n" % len(hs))
        f.flush()
threading.Thread(target=http_loop, daemon=True).start()
t = socket.socket(); t.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
t.bind(("0.0.0.0", 5300)); t.listen(16); print("authstub ready", flush=True)
while True:
    c, _ = t.accept(); threading.Thread(target=ctl, args=(c,), daemon=True).start()
