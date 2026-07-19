#!/usr/bin/env python3

import os
import json
import time
import random
import subprocess
import tempfile
import concurrent.futures
import urllib.parse
import base64


INPUT = "alive_nodes.txt"
OUTPUT = "result.txt"

SING_BOX="./sing-box"

TEST_URL="https://cp.cloudflare.com/generate_204"


if not os.path.exists(INPUT):
    print("缺少 alive_nodes.txt")
    exit(1)


with open(INPUT, errors="ignore") as f:
    nodes=[
        x.strip()
        for x in f
        if x.strip()
    ]


nodes=list(dict.fromkeys(nodes))

# 只测试 VLESS / VMESS
nodes=[
    n for n in nodes
    if n.startswith(
          (
            "vless://",
            "vmess://"
          )
       )
   ]

print(
    "读取节点:",
    len(nodes)
)


# 防止45分钟超时
random.shuffle(nodes)

nodes=nodes[:800]


def parse_node(node):

    try:

        if node.startswith("vless://"):

            u=urllib.parse.urlparse(node)

            uuid=u.username

            host=u.hostname

            port=u.port


            return {

                "type":"vless",

                "tag":"proxy",

                "server":host,

                "server_port":port,

                "uuid":uuid,

                "tls":{
                    "enabled":True,
                    "server_name":host
                }

            }



elif node.startswith("vmess://"):

    raw=node[8:]

    # 新格式 vmess://uuid@host:port?参数
    if "@" in raw:

        u=urllib.parse.urlparse(
            node
        )

        params=urllib.parse.parse_qs(
            u.query
        )


        return {

            "type":"vmess",

            "tag":"proxy",

            "server":u.hostname,

            "server_port":u.port,

            "uuid":u.username,

            "security":params.get(
                "encryption",
                ["auto"]
            )[0],

            "tls":{
                "enabled":
                params.get(
                    "security",
                    ["none"]
                )[0]=="tls"
            }

        }


    # 老格式 vmess://base64(json)

    decoded=base64.b64decode(
        raw+"==="
    ).decode(
        errors="ignore"
    )


    obj=json.loads(decoded)


    return {

        "type":"vmess",

        "tag":"proxy",

        "server":obj["add"],

        "server_port":int(
            obj["port"]
        ),

        "uuid":obj["id"],

        "security":obj.get(
            "scy",
            "auto"
        ),

        "tls":{
            "enabled":
            obj.get(
                "tls",
                ""
            )=="tls"
        }

    }


    except Exception:

        return None



def test_node(node):

    outbound=parse_node(node)

    if not outbound:
        return None


    port=random.randint(
        20000,
        50000
    )


    config={

        "log":{
            "level":"error"
        },


        "inbounds":[

            {

                "type":"mixed",

                "listen":"127.0.0.1",

                "listen_port":port

            }

        ],


        "outbounds":[

            outbound

        ]

    }


    tmp=tempfile.NamedTemporaryFile(
        mode="w",
        delete=False
    )


    json.dump(
        config,
        tmp
    )

    tmp.close()


    try:

        start=time.time()


        p=subprocess.Popen(
            [
                SING_BOX,
                "run",
                "-c",
                tmp.name
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )


        time.sleep(1)


        import urllib.request


        proxy=urllib.request.ProxyHandler(
            {
            "http":
            f"socks5://127.0.0.1:{port}",

            "https":
            f"socks5://127.0.0.1:{port}"
            }
        )


        opener=urllib.request.build_opener(
            proxy
        )


        opener.open(
            TEST_URL,
            timeout=8
        )


        delay=int(
            (time.time()-start)*1000
        )


        p.kill()


        os.unlink(
            tmp.name
        )


        return f"{delay}|{node}"


    except Exception:


        try:
            p.kill()
        except:
            pass


        try:
            os.unlink(
                tmp.name
            )
        except:
            pass


        return None




success=[]


print(
    "开始真实测速..."
)


with concurrent.futures.ThreadPoolExecutor(
    max_workers=20
) as exe:


    futures=[
        exe.submit(
            test_node,
            n
        )
        for n in nodes
    ]


    for f in concurrent.futures.as_completed(futures):

        r=f.result()

        if r:

            success.append(r)

            print(
                r.split("|")[0],
                "ms"
            )



success.sort(
    key=lambda x:int(x.split("|")[0])
)



with open(
    OUTPUT,
    "w",
    encoding="utf-8"
) as f:

    for x in success:

        f.write(
            x+"\n"
        )


print(
    "成功节点:",
    len(success)
)
