#!/usr/bin/env python3

import os
import json
import time
import random
import base64
import tempfile
import subprocess
import concurrent.futures
import urllib.parse


INPUT = "alive_nodes.txt"
OUTPUT = "result.txt"

SING_BOX = "./sing-box"

TEST_URL = "https://cp.cloudflare.com/generate_204"


# ==========================
# 初始化
# ==========================

if os.path.exists(OUTPUT):
    os.remove(OUTPUT)


if not os.path.exists(INPUT):

    print("缺少 alive_nodes.txt")
    exit(1)



with open(INPUT, errors="ignore") as f:

    nodes = [
        x.strip()
        for x in f
        if x.strip()
    ]



# 去重

nodes = list(dict.fromkeys(nodes))


# 只保留 VLESS VMESS

nodes = [
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



# 防止超时

random.shuffle(nodes)

nodes = nodes[:1000]



# ==========================
# 节点解析
# ==========================


def parse_node(node):

    try:


        # ------------------
        # VLESS
        # ------------------

        if node.startswith("vless://"):


            u = urllib.parse.urlparse(node)

            params = urllib.parse.parse_qs(
                u.query
            )


            security = params.get(
                "security",
                ["none"]
            )[0]


            return {


                "type":"vless",

                "tag":"proxy",

                "server":u.hostname,

                "server_port":u.port,

                "uuid":u.username,


                "tls":{

                    "enabled":
                    security == "tls",


                    "server_name":
                    params.get(
                        "sni",
                        [
                            u.hostname
                        ]
                    )[0]

                }


            }



        # ------------------
        # VMESS
        # ------------------

        elif node.startswith("vmess://"):


            raw = node[8:]


            try:

                decoded = base64.b64decode(
                    raw + "==="
                ).decode(
                    errors="ignore"
                )


                obj=json.loads(
                    decoded
                )


                return {


                    "type":"vmess",

                    "tag":"proxy",

                    "server":
                    obj.get("add"),


                    "server_port":
                    int(
                        obj.get(
                            "port"
                        )
                    ),


                    "uuid":
                    obj.get(
                        "id"
                    ),


                    "security":
                    obj.get(
                        "scy",
                        "auto"
                    ),


                    "tls":{


                        "enabled":
                        obj.get(
                            "tls",
                            ""
                        )=="tls",


                        "server_name":
                        obj.get(
                            "sni",
                            obj.get(
                                "host",
                                obj.get(
                                    "add"
                                )
                            )
                        )


                    }


                }


            except Exception:

                return None



    except Exception:

        return None



# ==========================
# 测试节点
# ==========================


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

                "listen":
                "127.0.0.1",

                "listen_port":
                port

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



    p=None


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

            (time.time()-start)
            *
            1000

        )



        return f"{delay}|{node}"



    except Exception:


        return None



    finally:


        if p:

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



# ==========================
# 并发测试
# ==========================


success=[]


print(
    "开始真实测速..."
)



with concurrent.futures.ThreadPoolExecutor(

    max_workers=20

) as executor:


    tasks=[

        executor.submit(
            test_node,
            n
        )

        for n in nodes

    ]


    for task in concurrent.futures.as_completed(tasks):


        r=task.result()


        if r:


            success.append(r)


            print(
                r.split("|")[0],
                "ms"
            )



success.sort(

    key=lambda x:
    int(
        x.split("|")[0]
    )

)



# ==========================
# 输出结果
# ==========================


with open(

    OUTPUT,

    "w",

    encoding="utf-8"

) as f:


    for x in success:

        f.write(
            x+"\n"
        )



print()

print(
    "成功节点:",
    len(success)
)


print(
    "已生成:",
    OUTPUT
)
