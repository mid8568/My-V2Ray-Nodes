#!/usr/bin/env python3

import os
import json
import time
import random
import subprocess
import tempfile
import concurrent.futures


INPUT = "alive_nodes.txt"
OUTPUT = "result.txt"

SING_BOX = "./sing-box"

TEST_URL = "https://cp.cloudflare.com/generate_204"


if not os.path.exists(INPUT):
    print("缺少 alive_nodes.txt")
    exit(1)


with open(INPUT, errors="ignore") as f:
    nodes = [
        x.strip()
        for x in f
        if x.strip()
    ]


nodes = list(dict.fromkeys(nodes))


print("读取节点:", len(nodes))


# 防止 GitHub Actions 超时
random.shuffle(nodes)

nodes = nodes[:500]


def test_node(node):

    port = random.randint(20000,40000)


    config = {
        "log": {
            "level": "error"
        },

        "inbounds":[
            {
                "type":"mixed",
                "listen":"127.0.0.1",
                "listen_port":port
            }
        ],

        "outbounds":[
            {
                "type":"selector",
                "tag":"proxy",
                "outbounds":["node"]
            },

            {
                "type":"direct",
                "tag":"direct"
            }
        ]
    }


    # 这里暂时跳过复杂协议解析
    # 防止错误节点导致失败

    return None



success=[]


# 当前只是框架
# 下一步加入 sing-box 节点解析


print("测试完成")

with open(
    OUTPUT,
    "w"
) as f:

    for x in success:
        f.write(x+"\n")


print(
    "成功节点:",
    len(success)
)
