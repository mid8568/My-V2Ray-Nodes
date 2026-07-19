#!/usr/bin/env python3
import os
from urllib.parse import urlparse

INPUT = "alive_nodes.txt"
OUTPUT = "result.txt"
FINAL_NODES_FILE = "nodes.txt" # 直接在这里定义最终文件名

def is_valid_vless(node):
    try:
        if node.startswith("vless://"):
            u = urlparse(node)
            return bool(u.hostname and u.username)
    except:
        return False
    return False

if __name__ == "__main__":
    if not os.path.exists(INPUT): 
        exit(1)
        
    with open(INPUT) as f: 
        raw_nodes = list(set(x.strip() for x in f if x.strip()))
        
    vless_nodes = []
    for node in raw_nodes:
        if not node.startswith("vless://"):
            continue
        if is_valid_vless(node):
            vless_nodes.append(node)

    # 1. 写入带有延迟格式的 result.txt (兼容你原本的某些旧逻辑)
    with open(OUTPUT, "w") as f:
        for node in vless_nodes:
            f.write(f"100|{node}\n")

    # 2. 【核心修复】直接在这里生成纯净、完整的最终 nodes.txt
    # 不做数量截断，把全部 3281 个 VLESS 原始节点完好无损地存进去
    with open(FINAL_NODES_FILE, "w") as f:
        for node in vless_nodes:
            f.write(node + "\n")

    print(f"清洗完成。已将 {len(vless_nodes)} 个完整的 VLESS 节点直接写入 {FINAL_NODES_FILE}")
