# Fake DNS that HOLDS every query until released over a TCP control port.
# UDP :53 queries; TCP :5300 control, one line per command:
#   WAIT <qname> <timeout>  -> "ok" once a query for qname is held, else "timeout"
#   RELEASE nx|a:<ip>       -> answers all held queries, "released N"
#   FLUSH                   -> drops held queries
import socket, struct, threading, sys, time
held = []           # (addr, data, qname)
seen = set()
cv = threading.Condition()
u = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); u.bind(("0.0.0.0", 53))
def qname_of(d):
    i, labels = 12, []
    while d[i]:
        n = d[i]; labels.append(d[i+1:i+1+n].decode()); i += n + 1
    return ".".join(labels).lower(), i + 5
def answer(data, mode, qend):
    tid = data[:2]; flags = 0x8180 | (3 if mode == "nx" else 0)
    q = data[12:qend]
    if mode == "nx":
        return tid + struct.pack(">HHHHH", flags, 1, 0, 0, 0) + q
    ip = socket.inet_aton(mode.split(":", 1)[1])
    rr = b"\xc0\x0c" + struct.pack(">HHIH", 1, 1, 1, 4) + ip
    return tid + struct.pack(">HHHHH", flags, 1, 1, 0, 0) + q + rr
def udp_loop():
    while True:
        data, addr = u.recvfrom(4096)
        try: name, qend = qname_of(data)
        except Exception: continue
        with cv:
            held.append((addr, data, name, qend)); seen.add(name); cv.notify_all()
def ctl(c):
    f = c.makefile("rw")
    for line in f:
        p = line.split()
        if not p: continue
        if p[0] == "WAIT":
            end = time.time() + float(p[2])
            with cv:
                ok = cv.wait_for(lambda: p[1].lower() in seen, timeout=max(0, end - time.time()))
            f.write("ok\n" if ok else "timeout\n")
        elif p[0] == "RELEASE":
            with cv:
                hs = held[:]; held.clear()
            for addr, data, name, qend in hs:
                u.sendto(answer(data, p[1], qend), addr)
            f.write("released %d\n" % len(hs))
        elif p[0] == "FLUSH":
            with cv: held.clear(); seen.clear()
            f.write("ok\n")
        f.flush()
    c.close()
threading.Thread(target=udp_loop, daemon=True).start()
t = socket.socket(); t.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
t.bind(("0.0.0.0", 5300)); t.listen(16)
print("fakedns ready", flush=True)
while True:
    c, _ = t.accept(); threading.Thread(target=ctl, args=(c,), daemon=True).start()
