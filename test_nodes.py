#!/usr/bin/env python3
import json, time, random, tempfile, subprocess, concurrent.futures, os, threading, socket, base64
from urllib.parse import urlparse, parse_qs

INPUT = "alive_nodes.txt"
OUTPUT = "result.txt"
# 混合使用两个出海最严苛的测速源，降低单一域名的 CDN 伪装误差
TEST_URLS = ["https://www.gstatic.com/generate_204", "https://www.google.com/generate_204"] 
write_lock = threading.Lock()

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
        if security in ("tls", "reality"): 
            out["tls"] = {"enabled": True, "server_name": q.get("sni", [host])[0]}
            if q.get("allowInsecure", [""])[0] in ("1", "true"): out["tls"]["insecure"] = True
        if security == "reality":
            pbk = q.get("pbk", [""])[0]
            if not pbk: return None
            out["tls"]["utls"] = {"enabled": True, "fingerprint": q.get("fp", ["chrome"])[0]}
            out["tls"]["reality"] = {"enabled": True, "public_key": pbk, "short_id": q.get("sid", [""])[0]}
        net = q.get("type", [""])[0]
        if net == "ws": out["transport"] = {"type": "ws", "path": q.get("path", ["/"])[0], "headers": {"Host": q.get("host", [host])[0]}}
        elif net == "grpc": out["transport"] = {"type": "grpc", "service_name": q.get("serviceName", [""])[0]}
        elif net == "httpupgrade": out["transport"] = {"type": "httpupgrade", "path": q.get("path", ["/"])[0], "host": [q.get("host", [host])[0]]}
        return out
    except: return None

def parse_vmess(uri):
    try:
        raw = uri.replace("vmess://", ""); obj = json.loads(b64decode(raw))
        out = {"type": "vmess", "tag": "proxy", "server": obj.get("add"), "server_port": int(obj.get("port")), "uuid": obj.get("id"), "security": obj.get("scy", "auto")}
        if obj.get("tls") in ("tls", 1, "1"):
            out["tls"] = {"enabled": True, "server_name": obj.get("sni", obj.get("host", obj.get("add")))}
        net = obj.get("net")
        if net == "ws": out["transport"] = {"type": "ws", "path": obj.get("path", "/"), "headers": {"Host": obj.get("host", obj.get("add"))}}
        elif net == "grpc": out["transport"] = {"type": "grpc", "service_name": obj.get("path", "")}
        return out
    except: return None

def parse_trojan(uri):
    try:
        u = urlparse(uri); q = parse_qs(u.query); host = u.hostname
        if not host or not u.username: return None
        out = {"type": "trojan", "tag": "proxy", "server": host, "server_port": int(u.port) if u.port else 443, "password": u.username, "tls": {"enabled": True, "server_name": q.get("sni", [host])[0]}}
        if q.get("allowInsecure", [""])[0] in ("1", "true"): out["tls"]["insecure"] = True
        net = q.get("type", [""])[0]
        if net == "ws": out["transport"] = {"type": "ws", "path": q.get("path", ["/"])[0], "headers": {"Host": q.get("host", [host])[0]}}
        elif net == "grpc": out["transport"] = {"type": "grpc", "service_name": q.get("serviceName", [""])[0]}
        return out
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
    outbound = parse(node)
    if not outbound: return
    port = get_port(); cfg = tempfile.mktemp(suffix=".json"); p = None
    try:
        with open(cfg, "w") as f: json.dump(make_config(outbound, port), f)
        p = subprocess.Popen(["./sing-box", "run", "-c", cfg], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        if not wait_port(port): return
        
        r = subprocess.run([
            "curl", "-4",
            "--connect-timeout", "6",
            "--max-time", "12",
            "-A", "Mozilla/5.0",
            "-x", f"http://127.0.0.1:{port}",
            "-s",
            "-o", "/dev/null",
            "-w", "%{http_code} %{time_total}",
            random.choice(TEST_URLS)
        ], capture_output=True, timeout=18)

        if r.returncode == 0:
            result = r.stdout.decode().strip().split()
            if len(result) >= 2:
                http_code = result[0]
                cost = float(result[1])

                if http_code in ["200", "204"]:
                    # 【核心优化策略】
                    # 如果是 VLESS 节点，给极宽的保留门槛（只要 12 秒内能响应全放行），确保那批好用的低延迟 VLESS 不被截断
                    if node.startswith("vless://") and cost < 12:
                        delay = int(cost * 1000)
                    # 如果是极易失效的 vmess/trojan 节点，提高筛选门槛（必须在 3.5 秒内完成连接才予保留）
                    elif cost < 3.5:
                        delay = int(cost * 1000)
                    else:
                        return

                    with write_lock:
                        with open(OUTPUT, "a") as f:
                            f.write(f"{delay}|{node}\n")
                            
    except Exception as e:
        pass
    finally:
        if p: p.kill()
        if os.path.exists(cfg): os.remove(cfg)

if __name__ == "__main__":
    if not os.path.exists(INPUT): exit(1)
    with open(INPUT) as f: nodes = list(set(x.strip() for x in f))
    random.shuffle(nodes)
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as pool:
        list(pool.map(test_node, nodes[:15000]))
