#!/usr/bin/env python3

import subprocess
import json
import os
import tempfile
import time
import concurrent.futures


INPUT = "nodes_all.txt"
OUTPUT = "result.txt"

TEST_URL = "https://www.gstatic.com/generate_204"


open(OUTPUT, "w").close()


def build_config(node):

    # 这里让 sing-box 直接读取 URI
    outbound = {
        "type": "urltest",
        "tag": "proxy",
        "outbounds": [
            "node"
        ]
    }


    config = {
        "log": {
            "level": "error"
        },

        "inbounds":[
            {
                "type":"mixed",
                "listen":"127.0.0.1",
                "listen_port":10808
            }
        ],

        "outbounds":[
            {
                "type":"direct",
                "tag":"direct"
            }
        ]
    }


    return config



def test_node(node):

    node=node.strip()

    if not node:
        return


    work=tempfile.mkdtemp()

    config_file=os.path.join(
        work,
        "config.json"
    )


    cfg=build_config(node)


    with open(config_file,"w") as f:
        json.dump(cfg,f)


    try:

        p=subprocess.Popen(
            [
                "./sing-box",
                "run",
                "-c",
                config_file
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )


        time.sleep(1)


        start=time.time()


        r=subprocess.run(
            [
                "curl",
                "-x",
                "socks5h://127.0.0.1:10808",
                "-o",
                "/dev/null",
                "-s",
                "-w",
                "%{http_code}",
                TEST_URL
            ],
            timeout=5,
            capture_output=True
        )


        cost=int((time.time()-start)*1000)


        if r.stdout.decode()=="204":

            print(
                "OK",
                cost,
                node[:40]
            )

            with open(OUTPUT,"a") as f:
                f.write(
                    f"{cost}ms {node}\n"
                )


    except Exception:

        pass


    finally:

        try:
            p.kill()
        except:
            pass



with open(INPUT,errors="ignore") as f:

    nodes=list(
        set(
            f.readlines()
        )
    )


# 限制数量
nodes=nodes[:300]


print(
    "测试节点:",
    len(nodes)
)



with concurrent.futures.ThreadPoolExecutor(
    max_workers=20
) as pool:

    pool.map(
        test_node,
        nodes
    )


print(
    "测速完成"
)
