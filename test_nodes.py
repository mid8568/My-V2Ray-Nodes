#!/usr/bin/env python3
import json, time, random, tempfile, subprocess, concurrent.futures, os, threading, socket, base64
from urllib.parse import urlparse, parse_qs

INPUT = "alive_nodes.txt"
OUTPUT = "result.txt"
TEST_URLS = ["https://www.gstatic.com/generate_204", "https://cp.cloudflare.com/generate_204"]
write_lock = threading.Lock()

# 清空结果文件
with open(OUTPUT, "w") as f: pass

def b64decode(x):
    try: return base64.urlsafe_b64decode(x + "===").decode(errors="ignore")
    except: return ""

def get_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close(); return port

def parse_vless(uri):
    try:
        u = urlparse(uri); q = parse_qs(u.query); host = u.hostname
        if not host: return None
        out = {"type": "vless", "tag": "proxy", "server": host, "server_port": int(u.port) if u.port else 443, "uuid": u.username, "encryption": "none", "packet_encoding": "xudp"}
        security = q.get("security", [""])[0]
        if security in ("tls", "reality"): out["tls"] = {"enabled": True, "server_name": q.get("sni", [host])[0]}
        if security == "reality":
            pbk = q.get("pbk", [""])[0]
            if not pbk: return None
            out["tls"]["utls"] = {"enabled": True, "fingerprint": q.get("fp", ["chrome"])[0]}
            out["tls"]["reality"] = {"enabled": True, "public_key": pbk, "short_id": q.get("sid", [""])[0]}
        return out
    except: return None

def parse_vmess(uri):
    try:
        raw = uri.replace("vmess://", ""); obj = json.loads(b64decode(raw))
        return {"type": "vmess", "tag": "proxy", "server": obj.get("add"), "server_port": int(obj.get("port")), "uuid": obj.get("id"), "security": obj.get("scy", "auto")}
    except: return None

def parse_trojan(uri):
    try:
        u = urlparse(uri); q = parse_qs(u.query); host = u.hostname
        if not host or not u.username: return None
        return {"type": "trojan", "tag": "proxy", "server": host, "server_port": int(u.port) if u.port else 443, "password": u.username, "tls": {"enabled": True, "server_name": q.get("sni", [host])[0]}}
    except: return None

def parse(uri):
    if uri.startswith("vless://"): return parse_vless(uri)
    if uri.startswith("vmess://"): return parse_vmess(uri)
    if uri.startswith("trojan://"): return parse_trojan(uri)
    return None

def make_config(node, port):
    return {"log": {"level": "error"}, "inbounds": [{"type": "mixed", "listen": "127.0.0.1", "listen_port": port}], "outbounds": [node, {"type": "direct", "tag": "direct"}]}

def wait_port(port):
    for _ in range(30):
        try:
            s = socket.socket(); s.settimeout(0.5); s.connect(("127.0.0.1", port)); s.close(); return True
        except: time.sleep(0.2)
    return False

def test_node(node):
    # 过滤黑名单
    if any(b in node for b in ["rooster465.autos", "gossipglove.com", "ignitelimit.com"]): return
    outbound = parse(node)
    if not outbound: return
    port = get_port(); cfg = tempfile.mktemp(suffix=".json"); p = None
    try:
        with open(cfg, "w") as f: json.dump(make_config(outbound, port), f)
        p = subprocess.Popen(["./sing-box", "run", "-c", cfg], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if not wait_port(port): return
        start = time.time()
        r = subprocess.run(["curl", "-4", "--connect-timeout", "2", "--max-time", "4", "-A", "Mozilla/5.0", "-x", f"http://127.0.0.1:{port}", "-s", "-o", "/dev/null", "-w", "%{http_code}", random.choice(TEST_URLS)], capture_output=True, timeout=6)
        if r.stdout.decode().strip() in ["200", "204"]:
            delay = int((time.time() - start) * 1000)
            with write_lock:
                with open(OUTPUT, "a") as f: f.write(f"{delay}|{node}\n")
    except: pass
    finally:
        if p: p.kill()
        if os.path.exists(cfg): os.remove(cfg)

if __name__ == "__main__":
    if not os.path.exists(INPUT): exit(1)
    with open(INPUT) as f: nodes = list(set(x.strip() for x in f))
    random.shuffle(nodes)
    with concurrent.futures.ThreadPoolExecutor(max_workers=80) as pool:
        list(pool.map(test_node, nodes[:15000]))
