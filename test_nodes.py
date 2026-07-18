#!/usr/bin/env python3

import json
import time
import random
import tempfile
import subprocess
import concurrent.futures
import os
import threading
import socket
import base64
from urllib.parse import urlparse, parse_qs

INPUT = "alive_nodes.txt"
OUTPUT = "result.txt"

# 严格使用 204 专用地址
TEST_URLS = [
    "https://www.gstatic.com/generate_204",
    "https://cp.cloudflare.com/generate_204"
]

write_lock = threading.Lock()

with open(OUTPUT, "w") as f:
    pass

def b64decode(x):
    try:
        return base64.urlsafe_b64decode(x + "===").decode(errors="ignore")
    except:
        return ""

def get_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port

def parse_vless(uri):
    try:
        u = urlparse(uri)
        q = parse_qs(u.query)
        host = u.hostname
        if not host: return None

        out = {
            "type": "vless",
            "tag": "proxy",
            "server": host,
            "server_port": int(u.port) if u.port else 443,
            "uuid": u.username,
            "encryption": "none",
            "packet_encoding": "xudp"
        }

        flow = q.get("flow", [""])[0]
        if flow: out["flow"] = flow

        security = q.get("security", [""])[0]
        if security in ("tls", "reality"):
            out["tls"] = {
                "enabled": True,
                "server_name": q.get("sni", [host])[0]
            }

        if security == "reality":
            pbk = q.get("pbk", [""])[0]
            if not pbk: return None
            out["tls"]["utls"] = {"enabled": True, "fingerprint": q.get("fp", ["chrome"])[0]}
            out["tls"]["reality"] = {"enabled": True, "public_key": pbk, "short_id": q.get("sid", [""])[0]}

        network = q.get("type", [""])[0]
        if network == "ws":
            out["transport"] = {"type": "ws", "path": q.get("path", ["/"])[0]}
        elif network == "grpc":
            out["transport"] = {"type": "grpc", "service_name": q.get("serviceName", [""])[0]}
        return out
    except:
        return None

def parse_vmess(uri):
    try:
        raw = uri.replace("vmess://", "")
        obj = json.loads(b64decode(raw))
        out = {
            "type": "vmess",
            "tag": "proxy",
            "server": obj.get("add"),
            "server_port": int(obj.get("port")),
            "uuid": obj.get("id"),
            "security": obj.get("scy", "auto")
        }
        if obj.get("net") == "ws":
            out["transport"] = {"type": "ws", "path": obj.get("path", "/")}
        if obj.get("tls") == "tls":
            out["tls"] = {"enabled": True, "server_name": obj.get("sni", obj.get("host", obj.get("add")))}
        return out
    except:
        return None

def parse_trojan(uri):
    try:
        u = urlparse(uri)
        q = parse_qs(u.query)
        host = u.hostname
        if not host or not u.username: return None

        out = {
            "type": "trojan",
            "tag": "proxy",
            "server": host,
            "server_port": int(u.port) if u.port else 443,
            "password": u.username,
            "tls": {
                "enabled": True,
                "server_name": q.get("sni", [host])[0]
            }
        }
        network = q.get("type", [""])[0]
        if network == "ws":
            out["transport"] = {"type": "ws", "path": q.get("path", ["/"])[0]}
        return out
    except:
        return None

def parse(uri):
    if uri.startswith("vless://"): return parse_vless(uri)
    if uri.startswith("vmess://"): return parse_vmess(uri)
    if uri.startswith("trojan://"): return parse_trojan(uri)
    return None

def make_config(node, port):
    return {
        "log": {"level": "error"},
        "inbounds": [{
            "type": "mixed",
            "listen": "127.0.0.1",
            "listen_port": port
        }],
        "outbounds": [
            node,
            {"type": "direct", "tag": "direct"}
        ]
    }

def wait_port(port):
    for _ in range(30):
        try:
            s = socket.socket()
            s.settimeout(0.5)
            s.connect(("127.0.0.1", port))
            s.close()
            return True
        except:
            time.sleep(0.2)
    return False

def test_node(node):
    # 过滤明显的诱饵域名，从源头上直接拉黑
    if "rooster465.autos" in node:
        return

    outbound = parse(node)
    if not outbound: return

    port = get_port()
    cfg = tempfile.mktemp(suffix=".json")
    p = None

    try:
        with open(cfg, "w") as f:
            json.dump(make_config(outbound, port), f)

        p = subprocess.Popen(
            ["./sing-box", "run", "-c", cfg],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        if not wait_port(port): return

        start = time.time()
        url = random.choice(TEST_URLS)

        # 核心修复点：严格限制状态码必须返回 204，并且只允许成功连接，防止网页劫持误判
        r = subprocess.run(
            [
                "curl", "-4", "--connect-timeout", "5", "--max-time", "8",
                "-A", "Mozilla/5.0",
                "-x", f"http://127.0.0.1:{port}",
                "-s", "-o", "/dev/null", "-w", "%{http_code}", url
            ],
            capture_output=True, timeout=10
        )

        delay = int((time.time() - start) * 1000)
        code = r.stdout.decode().strip()

        # 诱饵节点通常返回 200，真正的 204 才是能通外网的核心节点
        if code == "204":
            with write_lock:
                with open(OUTPUT, "a") as f:
                    f.write(f"{delay}|{node}\n")
    except:
        pass
    finally:
        try:
            if p: p.kill()
        except: pass
        try:
            os.remove(cfg)
        except: pass

if __name__ == "__main__":
    if not os.path.exists(INPUT):
        print(f"缺少 {INPUT}")
        exit(1)

    with open(INPUT, errors="ignore") as f:
        nodes = list(set(x.strip() for x in f if x.strip()))

    print("待测试总数:", len(nodes))
    random.shuffle(nodes)
    
    # 增加实际测试量，扩大几率
    nodes = nodes[:25000]
    print("实际测试池:", len(nodes))

    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as pool:
        list(pool.map(test_node, nodes))

    if os.path.exists(OUTPUT):
        with open(OUTPUT, errors="ignore") as f:
            lines = f.readlines()

        good = []
        for line in lines:
            try:
                if "|" in line:
                    ms = int(line.split("|")[0])
                    good.append((ms, line))
            except: pass

        good.sort(key=lambda x: x[0])

        with open(OUTPUT, "w") as f:
            for _, line in good:
                f.write(line)

        print(f"测试完成，筛选出可用节点: {len(good)} 个")
