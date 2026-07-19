#!/usr/bin/env python3
import os
import threading
from urllib.parse import urlparse

INPUT = "alive_nodes.txt"
OUTPUT = "result.txt"

with open(OUTPUT, "w") as f: pass

def is_valid_vless(node):
    """
    严格校验 VLESS 格式，确保参数完整性
    """
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
        # 去重并清洗空格
        raw_nodes = list(set(x.strip() for x in f if x.strip()))
        
    vless_nodes = []
    
    for node in raw_nodes:
        # 【核心修改】只留下 VLESS，强行过滤掉 trojan 和 vmess
        if not node.startswith("vless://"):
            continue
            
        if is_valid_vless(node):
            vless_nodes.append(node)

    # 【核心调整】不对 VLESS 的数量做任何截断限制，抓到多少就放出多少
    with open(OUTPUT, "w") as f:
        for node in vless_nodes:
            f.write(f"100|{node}\n")

    print(f"清洗完成。已剔除全部 Trojan 和 VMess。共保留 {len(vless_nodes)} 个完整格式的 VLESS 节点送往本地。")
