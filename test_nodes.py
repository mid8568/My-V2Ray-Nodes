#!/usr/bin/env python3
import json
import os
import threading
import base64
from urllib.parse import urlparse

INPUT = "alive_nodes.txt"
OUTPUT = "result.txt"
write_lock = threading.Lock()

# 清空并初始化结果文件
with open(OUTPUT, "w") as f: pass

def b64decode(x):
    try: 
        return base64.urlsafe_b64decode(x + "===").decode(errors="ignore")
    except: 
        return ""

def is_valid_node(node):
    """
    基础格式校验，确保导出的节点参数是完好、无损且可解析的
    """
    try:
        if node.startswith("vless://"):
            u = urlparse(node)
            return bool(u.hostname and u.username)
        elif node.startswith("vmess://"):
            raw = node.replace("vmess://", "")
            obj = json.loads(b64decode(raw))
            return bool(obj.get("add") and obj.get("id"))
    except:
        return False
    return False

if __name__ == "__main__":
    if not os.path.exists(INPUT): 
        exit(1)
        
    with open(INPUT) as f: 
        # 去重并清洗两端空格
        raw_nodes = list(set(x.strip() for x in f if x.strip()))
        
    valid_nodes = []
    for node in raw_nodes:
        # 1. 彻底不要 Trojan
        if node.startswith("trojan://"):
            continue
            
        # 2. 校验 VLESS 和 VMess 的格式是否完整
        if is_valid_node(node):
            valid_nodes.append(node)

    # 限制最大输出数量，防止订阅撑爆 v2rayN（通常 2000-3000 个优质种子即可）
    output_nodes = valid_nodes[:3000]

    with open(OUTPUT, "w") as f:
        for node in output_nodes:
            # 伪装一个固定的延迟分值（比如 100），让后续的 yml 脚本能正常按格式处理它
            f.write(f"100|{node}\n")

    print(f"云端清洗完成。共注入 {len(output_nodes)} 个完整格式的 VLESS/VMess 节点，等待本地 v2rayN 测速。")
