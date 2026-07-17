#!/usr/bin/env python3

import subprocess
import json
import os
import time
import tempfile


INPUT="nodes_all.txt"
OUTPUT="result.txt"


open(OUTPUT,"w").close()


def test_node(node):

    work=tempfile.mkdtemp()

    config=f"""
{{
"log": {{
"level":"error"
}},
"inbounds":[
{{
"type":"mixed",
"listen":"127.0.0.1",
"listen_port":10808
}}
],
"outbounds":[
{{
"type":"urltest",
"tag":"proxy",
"outbounds":["node"]
}},
{{
"type":"direct",
"tag":"direct"
}}
]
}}
"""

    with open(work+"/config.json","w") as f:
        f.write(config)


    # 这里调用 sing-box
    p=subprocess.Popen(
        [
        "./sing-box",
        "run",
        "-c",
        work+"/config.json"
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )


    time.sleep(2)


    try:

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
        "https://www.gstatic.com/generate_204"
        ],
        timeout=8,
        capture_output=True
        )


        code=r.stdout.decode()


        if code=="204":

            with open(OUTPUT,"a") as f:
                f.write(node+"\n")

    except:
        pass


    p.kill()



with open(INPUT,errors="ignore") as f:

    nodes=f.readlines()


for i,node in enumerate(nodes[:200]):

    node=node.strip()

    print(
    "testing",
    i+1,
    "/",
    len(nodes[:200])
    )

    test_node(node)
