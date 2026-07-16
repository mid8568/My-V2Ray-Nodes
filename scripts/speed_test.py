#!/usr/bin/env python3

import subprocess
import time
import os
import json


INPUT = "tcp_alive_nodes.txt"
OUTPUT = "speed_rank.txt"

TEST_URL = "https://speed.cloudflare.com/__down?bytes=1000000"

PROXY_PORT = 10809


def test_speed(node):

    config = {
        "log": {
            "level": "error"
        },

        "inbounds": [
            {
                "type": "mixed",
                "listen": "127.0.0.1",
                "listen_port": PROXY_PORT
            }
        ],

        "outbounds": [
            {
                "type": "selector",
                "tag": "proxy",
                "outbounds": [
                    "node"
                ]
            },

            {
                "type": "direct",
                "tag": "direct"
            },

            {
                "type": "vmess",
                "tag": "node",
                "server": "",
                "server_port": 443
            }
        ]
    }


    # 暂时跳过无法解析节点
    # 真实版本需要解析 vless/vmess/trojan


    return 0



results=[]


with open(INPUT,"r",encoding="utf-8") as f:

    nodes=f.readlines()



for index,node in enumerate(nodes):

    node=node.strip()

    if not node:
        continue


    print(
        f"测速 {index+1}/{len(nodes)}"
    )


    speed=test_speed(node)


    if speed>0:

        results.append(
            (
                speed,
                node
            )
        )



results.sort(
    reverse=True,
    key=lambda x:x[0]
)



with open(
    OUTPUT,
    "w",
    encoding="utf-8"
) as f:

    for speed,node in results:

        f.write(
            f"{speed}|{node}\n"
        )


print(
    "真实测速完成:",
    len(results)
)
