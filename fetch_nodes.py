import os
import requests
import base64
import json
import socket
import concurrent.futures

# 测试单个节点的 TCP 连通性
def test_tcp(address, port, timeout=3):
    try:
        # 解析域名获取 IP，防止有些节点因为 DNS 无法解析卡死
        ip = socket.gethostbyname(address)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((ip, int(port)))
        s.close()
        return True
    except Exception:
        return False

# 解析 vmess 节点获取地址和端口
def parse_vmess(node_str):
    try:
        b64_data = node_str.replace("vmess://", "")
        # 补齐 base64 填充
        missing_padding = len(b64_data) % 4
        if missing_padding:
            b64_data += '=' * (4 - missing_padding)
        json_str = base64.b64decode(b64_data).decode('utf-8')
        config = json.loads(json_str)
        return config.get("add"), config.get("port")
    except Exception:
        return None, None

# 统一测速函数
def check_node_alive(node_str):
    if node_str.startswith("vmess://"):
        add, port = parse_vmess(node_str)
        if add and port:
            if test_tcp(add, port):
                return node_str
    elif node_str.startswith(("ss://", "vless://", "trojan://", "ssr://")):
        # 简单解析 ss/vless/trojan 的地址和端口
        try:
            # 移除协议头并去掉别名部分（#号后面的内容）
            clean_str = node_str.split("://")[1].split("#")[0]
            if "@" in clean_str:
                clean_str = clean_str.split("@")[1]
            # 提取 host:port
            host_port = clean_str.split("/")[0]
            if ":" in host_port:
                add = host_port.split(":")[0]
                port = host_port.split(":")[1]
                if test_tcp(add, port):
                    return node_str
        except Exception:
            pass
    return None

def fetch_and_filter_nodes():
    urls = [
        "https://githubusercontent.com",
        "https://githubusercontent.com"
    ]
    
    all_nodes = []
    print("开始抓取全网免费节点...")
    for url in urls:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                content = response.text.strip()
                try:
                    decoded = base64.b64decode(content + '=' * (-len(content) % 4)).decode('utf-8')
                    nodes = decoded.splitlines()
                except Exception:
                    nodes = content.splitlines()
                
                for node in nodes:
                    if node.startswith(("vmess://", "vless://", "ss://", "ssr://", "trojan://")):
                        all_nodes.append(node)
        except Exception as e:
            print(f"抓取 {url} 失败: {e}")
            
    unique_nodes = list(set(all_nodes))
    print(f"去重完成，抓取到 {len(unique_nodes)} 个初始节点，开始并发测速筛选...")

    alive_nodes = []
    # 开启 30 个线程并发测速，防止节点过多时导致 Actions 运行超时
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        results = executor.map(check_node_alive, unique_nodes)
        for res in results:
            if res:
                alive_nodes.append(res)

    print(f"测速完成！过滤掉死节点后，剩余可用活节点: {len(alive_nodes)} 个。")
    
    # 写入文件
    with open("nodes.txt", "w", encoding="utf-8") as f:
        for node in alive_nodes:
            f.write(node + "\n")
    print("可用节点已写入 nodes.txt")

if __name__ == "__main__":
    fetch_and_filter_nodes()
