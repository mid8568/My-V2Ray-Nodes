#!/usr/bin/env python3
import json
import os
import threading
import base64
from urllib.parse import urlparse

INPUT = "alive_nodes.txt"
OUTPUT = "result.txt"

with open(OUTPUT, "w") as f: pass

def b64decode(x):
    try: 
        return base64.urlsafe_b64decode(x + "===").decode(errors="ignore")
    except: 
        return ""

def is_valid_node(node):
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
        raw_nodes = list(set(x.strip() for x in f if x.strip()))
        
    vless_nodes = []
    vmess_nodes = []
    
    for node in raw_nodes:
        if node.startswith("trojan://"):
            continue
            
        if is_valid_node(node):
            # 将节点按协议分流
            if node.startswith("vless://"):
                vless_nodes.append(node)
            else:
                vmess_nodes.append(node)

    # 【核心调整】将 VLESS 节点全部打包放在最前面，VMess 紧随其后
    # 扩大总量限制到 5000，确保你想找的 VLESS 节点 100% 被收入进去
    final_nodes = (vless_nodes + vmess_nodes)[:5000]

    with open(OUTPUT, "w") as f:
        for node in final_nodes:
            f.write(f"100|{node}\n")

    print(f"清洗完成。VLESS数量: {len(vless_nodes)}，VMess数量: {len(vmess_nodes)}。已优先将 VLESS 排在首位。")
