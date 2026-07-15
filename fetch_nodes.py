import os
import requests
import base64
import json
import socket
import concurrent.futures

# 增强型：测试单个节点的 TCP 连通性
def test_tcp(address, port, timeout=2):
    if not address or not port:
        return False
    try:
        # 解析域名获取 IP
        ip = socket.gethostbyname(str(address).strip())
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((ip, int(port)))
        s.close()
        return True
    except Exception:
        return False

# 解析 vmess 节点
def parse_vmess(node_str):
    try:
        b64_data = node_str.replace("vmess://", "").strip()
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
    node_str = node_str.strip()
    if not node_str:
        return None
        
    if node_str.startswith("vmess://"):
        add, port = parse_vmess(node_str)
        if add and port and test_tcp(add, port):
            return node_str
            
    elif node_str.startswith(("ss://", "vless://", "trojan://", "ssr://")):
        try:
            # 兼容更多特殊字符的简易切分提取端口
            clean_str = node_str.split("://")[1].split("#")[0]
            if "@" in clean_str:
                clean_str = clean_str.split("@")[1]
            if "?" in clean_str:
                clean_str = clean_str.split("?")[0]
                
            if ":" in clean_str:
                parts = clean_str.split(":")
                add = parts[0]
                # 兼容类似 host:port/path 的情况
                port = parts[1].split("/")[0]
                if test_tcp(add, port):
                    return node_str
        except Exception:
            pass
    return None

def fetch_and_filter_nodes():
    # 增加更多备用、高质量且在 GitHub 环境下容易测通的源
    urls = [
        "https://githubusercontent.com",
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
                    # 尝试全面 Base64 解码整个订阅
                    decoded = base64.b64decode(content + '=' * (-len(content) % 4)).decode('utf-8')
                    nodes = decoded.splitlines()
                except Exception:
                    nodes = content.splitlines()
                
                for node in nodes:
                    if node.startswith(("vmess://", "vless://", "ss://", "ssr://", "trojan://")):
                        all_nodes.append(node.strip())
        except Exception as e:
            print(f"抓取 {url} 失败: {e}")
            
    unique_nodes = list(set([n for n in all_nodes if n]))
    total_count = len(unique_nodes)
    print(f"去重完成，共抓取到 {total_count} 个初始节点。开始并发测速...")

    if total_count == 0:
        print("警告：未能从订阅源成功抓取到任何节点，请检查源网址是否有效。")
        return

    alive_nodes = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=40) as executor:
        results = executor.map(check_node_alive, unique_nodes)
        for res in results:
            if res:
                alive_nodes.append(res)

    print(f"测速完成！剩余可用活节点: {len(alive_nodes)} 个。")
    
    # 【核心修复：保底机制】如果测速后全灭，保留前 30 个原始节点防止文件空白
    if len(alive_nodes) == 0:
        print("⚠️ 提示：GitHub 测速全部超时，启动保底机制，直接写入原始节点！")
        alive_nodes = unique_nodes[:30]
    
    # 写入文件
    with open("nodes.txt", "w", encoding="utf-8") as f:
        for node in alive_nodes:
            f.write(node + "\n")
    print("可用节点已写入 nodes.txt")

if __name__ == "__main__":
    fetch_and_filter_nodes()
