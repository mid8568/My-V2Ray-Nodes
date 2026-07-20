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
import urllib.request


INPUT = "alive_nodes.txt"
OUTPUT = "result.txt"

SING_BOX = "./sing-box"

TEST_URL = "https://www.gstatic.com/generate_204"


# ======================
# 初始化
# ======================

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



nodes = list(dict.fromkeys(nodes))



# 只保留 VLESS VMESS

nodes = [

    n for n in nodes

    if n.startswith(
        (
            "vless://",
            "vmess://",
            "trojan://",
            "ss://"
        )
    )

]


print(
    "读取节点:",
    len(nodes)
)



random.shuffle(nodes)


# 防止超时
nodes = nodes[:8000]



# ======================
# 解析节点
# ======================


def parse_node(node):

    try:
        # -----------------
        # TROJAN
        # -----------------

        if node.startswith("trojan://"):


            u = urllib.parse.urlparse(node)


            params = urllib.parse.parse_qs(
                u.query
            )


            outbound = {

                "type":
                "trojan",

                "tag":
                "proxy",

                "server":
                u.hostname,

                "server_port":
                u.port,

                "password":
                u.username

            }



            if params.get(
                "sni"
            ):


                outbound["tls"]={

                    "enabled":
                    True,

                    "server_name":
                    params["sni"][0]

                }


            return outbound

        # -----------------
        # Shadowsocks
        # -----------------

        if node.startswith("ss://"):


            raw=node[5:]


            # 去掉 fragment

            raw=raw.split("#")[0]


            try:


                decoded=base64.urlsafe_b64decode(
                    raw+"=="
                ).decode()


                method_password,server=decoded.split(
                    "@"
                )


                method,password=method_password.split(
                    ":",
                    1
                )


                host,port=server.split(
                    ":"
                )


                outbound={


                    "type":
                    "shadowsocks",


                    "tag":
                    "proxy",


                    "server":
                    host,


                    "server_port":
                    int(port),


                    "method":
                    method,


                    "password":
                    password

                }


                return outbound


            except:


                return None

        # -----------------
        # VLESS
        # -----------------

        if node.startswith("vless://"):


            u = urllib.parse.urlparse(node)


            params = urllib.parse.parse_qs(
                u.query
            )


            outbound = {


                "type":
                "vless",


                "tag":
                "proxy",


                "server":
                u.hostname,


                "server_port":
                u.port,


                "uuid":
                u.username

            }



            security = params.get(
                "security",
                ["none"]
            )[0]



            if security == "tls":


                outbound["tls"] = {


                    "enabled":
                    True,


                    "server_name":
                    params.get(
                        "sni",
                        [
                            u.hostname
                        ]
                    )[0]

                }



            # websocket


            if params.get(
                "type",
                ["tcp"]
            )[0] == "ws":



                outbound["transport"] = {


                    "type":
                    "ws",


                    "path":
                    params.get(
                        "path",
                        ["/"]
                    )[0]

                }



                host=params.get(
                    "host",
                    []
                )


                if host:


                    outbound["transport"]["headers"]={

                        "Host":
                        host[0]

                    }



            return outbound




        # -----------------
        # VMESS
        # -----------------

        if node.startswith("vmess://"):



            raw=node[8:]


            decoded=base64.b64decode(

                raw+"==="

            ).decode(

                errors="ignore"

            )


            obj=json.loads(
                decoded
            )



            outbound={


                "type":
                "vmess",


                "tag":
                "proxy",


                "server":
                obj.get(
                    "add"
                ),


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
                )

            }



            # TLS


            if obj.get(
                "tls",
                ""
            ) == "tls":



                outbound["tls"]={


                    "enabled":
                    True,


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



            # WS


            if obj.get(
                "net"
            ) == "ws":



                outbound["transport"]={


                    "type":
                    "ws",


                    "path":
                    obj.get(
                        "path",
                        "/"
                    )

                }



                if obj.get(
                    "host"
                ):


                    outbound["transport"]["headers"]={


                        "Host":
                        obj["host"]

                    }



            return outbound



    except Exception:


        return None



# ======================
# 测试
# ======================


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

            "level":
            "error"

        },


        "inbounds":[

            {

                "type":
                "mixed",


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



    process=None


    try:


        start=time.time()



        process=subprocess.Popen(

            [

                SING_BOX,

                "run",

                "-c",

                tmp.name

            ],


            stdout=subprocess.DEVNULL,


            stderr=subprocess.DEVNULL

        )



        time.sleep(3)



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



        response=opener.open(

            TEST_URL,

            timeout=8

        )



        if response.status not in [200,204]:

            return None



        delay=int(

            (time.time()-start)*1000

        )



        return f"{delay}|{node}"



    except Exception:


        return None



    finally:


        if process:


            try:

                process.kill()

            except:

                pass



        try:

            os.unlink(
                tmp.name
            )

        except:

            pass




# ======================
# 并发测速
# ======================


success=[]


print(
    "开始真实测速..."
)



with concurrent.futures.ThreadPoolExecutor(

    max_workers=80

) as executor:



    futures=[

        executor.submit(
            test_node,
            n
        )

        for n in nodes

    ]



    for future in concurrent.futures.as_completed(futures):


        result=future.result()


        if result:


            success.append(result)


            print(
                result.split("|")[0],
                "ms"
            )




success.sort(

    key=lambda x:
    int(
        x.split("|")[0]
    )

)




# ======================
# 输出
# ======================


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
    "生成:",
    OUTPUT
)
