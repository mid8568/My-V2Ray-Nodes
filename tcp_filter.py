#!/usr/bin/env python3
import os

INPUT = "nodes_all.txt"
OUTPUT = "alive_nodes.txt"

if not os.path.exists(INPUT):
    print("缺少 nodes_all.txt")
    exit(1)

with open(INPUT, errors="ignore") as f:
    raw_nodes = [x.strip() for x in f if x.strip()]

# 基础去重，只留下 vless 节点（从源头减轻后续处理压力）
nodes = []
for n in set(raw_nodes):
    if n.startswith("vless://"):
        nodes.append(n)

print(f"原始抓取总数: {len(raw_nodes)} | 筛选出的 VLESS 总数: {len(nodes)}")

# 直接输出所有 VLESS 节点，不做任何数量截断
with open(OUTPUT, "w") as f:
    for n in nodes:
        f.write(n + "\n")

print("已成功将所有 VLESS 节点送入下一步。")
