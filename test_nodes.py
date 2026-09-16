#!/usr/bin/env python3
import base64
import concurrent.futures
import json
import os
import random
import socket
import subprocess
import tempfile
import time
import urllib.parse
import urllib.request

INPUT = "nodes_all.txt"
OUTPUT = "result.txt"
SING_BOX = "./sing-box"

TEST_URL = "https://www.gstatic.com/generate_204"

MAX_NODES = 2000
MAX_WORKERS = 20
START_TIMEOUT = 8
TEST_TIMEOUT = 12


def b64decode_text(value):
    if not value:
        return ""
    try:
        value = value.strip()
        value += "=" * (-len(value) % 4)
        return base64.b64decode(value).decode("utf-8", errors="ignore")
    except Exception:
        return ""


def q(params, key, default=None):
    value = params.get(key)
    if not value:
        return default
    return value[0]


def safe_int(value, default):
    try:
        return int(value)
    except Exception:
        return default


def parse_vless(uri):
    try:
        u = urllib.parse.urlparse(uri)
        if not u.hostname or not u.port or not u.username:
            return None

        p = urllib.parse.parse_qs(u.query, keep_blank_values=True)
        proxy = {
            "type": "vless",
            "server": u.hostname,
            "server_port": u.port,
            "uuid": urllib.parse.unquote(u.username),
        }

        network = q(p, "type", "tcp")
        if network not in ("tcp", "ws", "grpc"):
            network = "tcp"

        proxy["network"] = network

        security = (q(p, "security", "") or "").lower()

        if security == "tls":
            proxy["tls"] = {
                "enabled": True,
                "server_name": q(p, "sni") or q(p, "host") or u.hostname,
            }

        elif security == "reality":
            public_key = q(p, "pbk")
            short_id = q(p, "sid", "")
            server_name = q(p, "sni") or q(p, "host") or u.hostname

            if not public_key:
                return None

            proxy["tls"] = {
                "enabled": True,
                "server_name": server_name,
                "reality": {
                    "enabled": True,
                    "public_key": public_key,
                    "short_id": short_id,
                },
                "utls": {
                    "enabled": True,
                    "fingerprint": q(p, "fp", "chrome"),
                },
            }

        if q(p, "flow"):
            proxy["flow"] = q(p, "flow")

        if network == "ws":
            proxy["transport"] = {
                "type": "ws",
                "path": q(p, "path", "/"),
            }
            host = q(p, "host")
            if host:
                proxy["transport"]["headers"] = {"Host": host}

        elif network == "grpc":
            proxy["transport"] = {
                "type": "grpc",
                "service_name": q(p, "serviceName", ""),
            }

        return proxy
    except Exception:
        return None


def parse_vmess(uri):
    try:
        raw = uri[8:].split("#", 1)[0]
        data = json.loads(b64decode_text(raw))
        server = data.get("add")
        port = safe_int(data.get("port"), 0)
        uuid = data.get("id")

        if not server or not port or not uuid:
            return None

        proxy = {
            "type": "vmess",
            "server": server,
            "server_port": port,
            "uuid": uuid,
            "security": data.get("scy") or "auto",
        }

        network = data.get("net") or "tcp"

        if network == "ws":
            proxy["transport"] = {
                "type": "ws",
                "path": data.get("path") or "/",
            }
            host = data.get("host")
            if host:
                proxy["transport"]["headers"] = {"Host": host}

        elif network == "grpc":
            proxy["transport"] = {
                "type": "grpc",
                "service_name": data.get("path") or "",
            }

        elif network != "tcp":
            return None

        tls = str(data.get("tls", "")).lower()
        if tls in ("tls", "true", "1"):
            proxy["tls"] = {
                "enabled": True,
                "server_name": data.get("sni") or data.get("host") or server,
            }

        return proxy
    except Exception:
        return None


def parse_trojan(uri):
    try:
        u = urllib.parse.urlparse(uri)
        if not u.hostname or not u.port or not u.username:
            return None

        p = urllib.parse.parse_qs(u.query, keep_blank_values=True)

        proxy = {
            "type": "trojan",
            "server": u.hostname,
            "server_port": u.port,
            "password": urllib.parse.unquote(u.username),
            "tls": {
                "enabled": True,
                "server_name": q(p, "sni") or u.hostname,
            },
        }

        network = q(p, "type", "tcp")

        if network == "ws":
            proxy["transport"] = {
                "type": "ws",
                "path": q(p, "path", "/"),
            }
            host = q(p, "host")
            if host:
                proxy["transport"]["headers"] = {"Host": host}

        elif network == "grpc":
            proxy["transport"] = {
                "type": "grpc",
                "service_name": q(p, "serviceName", ""),
            }

        elif network != "tcp":
            return None

        return proxy
    except Exception:
        return None


def parse_ss(uri):
    try:
        u = urllib.parse.urlparse(uri)
        if not u.hostname or not u.port:
            return None

        userinfo = urllib.parse.unquote(u.username or "")
        decoded = b64decode_text(userinfo) if ":" not in userinfo else userinfo

        if ":" not in decoded:
            return None

        method, password = decoded.split(":", 1)

        return {
            "type": "shadowsocks",
            "server": u.hostname,
            "server_port": u.port,
            "method": method,
            "password": password,
        }
    except Exception:
        return None


def parse_hy2(uri):
    try:
        u = urllib.parse.urlparse(uri)
        if not u.hostname:
            return None

        p = urllib.parse.parse_qs(u.query, keep_blank_values=True)
        proxy = {
            "type": "hysteria2",
            "server": u.hostname,
            "server_port": u.port or 443,
            "password": urllib.parse.unquote(u.username or ""),
        }

        server_name = q(p, "sni")
        insecure = (q(p, "insecure", "0") or "0").lower()

        proxy["tls"] = {
            "enabled": True,
            "server_name": server_name or u.hostname,
            "insecure": insecure in ("1", "true"),
        }

        return proxy
    except Exception:
        return None


def parse_node(uri):
    lower = uri.lower()
    if lower.startswith("vless://"):
        return parse_vless(uri)
    if lower.startswith("vmess://"):
        return parse_vmess(uri)
    if lower.startswith("trojan://"):
        return parse_trojan(uri)
    if lower.startswith("ss://"):
        return parse_ss(uri)
    if lower.startswith("hy2://") or lower.startswith("hysteria2://"):
        return parse_hy2(uri)
    return None


def find_free_port():
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def wait_port(port, timeout):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return True
        except Exception:
            time.sleep(0.15)
    return False


def build_config(proxy):
    port = find_free_port()

    config = {
        "log": {
            "level": "error"
        },
        "inbounds": [
            {
                "type": "mixed",
                "tag": "mixed-in",
                "listen": "127.0.0.1",
                "listen_port": port,
            }
        ],
        "outbounds": [
            dict(proxy, tag="proxy"),
            {
                "type": "direct",
                "tag": "direct"
            }
        ],
        "route": {
            "final": "proxy"
        }
    }

    return config, port


def test_one(item):
    index, uri = item
    proxy = parse_node(uri)

    if not proxy:
        return None

    fd, config_path = tempfile.mkstemp(prefix="sb-", suffix=".json")
    os.close(fd)

    process = None

    try:
        config, local_port = build_config(proxy)

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False)

        check = subprocess.run(
            [SING_BOX, "check", "-c", config_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )

        if check.returncode != 0:
            return None

        process = subprocess.Popen(
            [SING_BOX, "run", "-c", config_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        if not wait_port(local_port, START_TIMEOUT):
            return None

        opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({
                "http": f"http://127.0.0.1:{local_port}",
                "https": f"http://127.0.0.1:{local_port}",
            })
        )

        request = urllib.request.Request(
            TEST_URL,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Connection": "close",
            },
        )

        start = time.monotonic()

        with opener.open(request, timeout=TEST_TIMEOUT) as response:
            status = response.getcode()

        delay = int((time.monotonic() - start) * 1000)

        if status not in (200, 204):
            return None

        return delay, uri

    except Exception:
        return None

    finally:
        if process is not None:
            try:
                process.terminate()
                process.wait(timeout=2)
            except Exception:
                try:
                    process.kill()
                except Exception:
                    pass

        try:
            os.remove(config_path)
        except Exception:
            pass


def main():
    if not os.path.exists(INPUT):
        raise SystemExit(f"错误：找不到 {INPUT}")

    if not os.path.exists(SING_BOX):
        raise SystemExit(f"错误：找不到 {SING_BOX}")

    with open(INPUT, "r", encoding="utf-8", errors="ignore") as f:
        nodes = [x.strip() for x in f if x.strip()]

    nodes = list(dict.fromkeys(nodes))
    random.shuffle(nodes)
    nodes = nodes[:MAX_NODES]

    print("读取节点:", len(nodes))
    print("并发测试:", MAX_WORKERS)

    # 先确认 sing-box 本身可以运行
    version = subprocess.run(
        [SING_BOX, "version"],
        capture_output=True,
        text=True,
        timeout=5,
    )
    print(version.stdout.strip())

    results = []

    items = list(enumerate(nodes, 1))

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=MAX_WORKERS
    ) as executor:
        futures = {
            executor.submit(test_one, item): item
            for item in items
        }

        done = 0

        for future in concurrent.futures.as_completed(futures):
            done += 1
            result = future.result()

            if result:
                delay, uri = result
                results.append((delay, uri))
                print(
                    f"[{done}/{len(items)}] 可用 {delay} ms: "
                    f"{uri[:100]}",
                    flush=True,
                )
            elif done % 50 == 0:
                print(
                    f"[{done}/{len(items)}] 已测试，当前可用 {len(results)}",
                    flush=True,
                )

    results.sort(key=lambda x: x[0])

    with open(OUTPUT, "w", encoding="utf-8") as f:
        for delay, uri in results:
            f.write(f"{delay}|{uri}\n")

    print("")
    print("测试节点:", len(nodes))
    print("可用节点:", len(results))
    print("结果文件:", OUTPUT)

    if not results:
        raise SystemExit("错误：没有通过真实 HTTPS 测试的节点")


if __name__ == "__main__":
    main()
