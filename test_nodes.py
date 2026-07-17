#!/usr/bin/env python3

import json
import os
import time
import base64
import tempfile
import subprocess
import concurrent.futures
from urllib.parse import urlparse, parse_qs, unquote


INPUT = "nodes_all.txt"
OUTPUT = "result.txt"

TEST_URL = "https://www.gstatic.com/generate_204"


open(OUTPUT,"w").close()


def parse_node(uri):

    try:

        if uri.startswith("vless://"):

            u=urlparse(uri)

            q=parse_qs(u.query)


            return {
                "type":"vless",
                "tag":"node",

                "server":u.hostname,
                "server_port":u.port,

                "uuid":u.username,

                "tls":{
                    "enabled": q.get("security",[""]) [0]=="tls"
                }
            }


        elif uri.startswith("trojan://"):

            u=urlparse(uri)

            return {

                "type":"trojan",
                "tag":"node",

                "server":u.hostname,
                "server_port":u.port,

                "password":u.username,

                "tls":{
                    "enabled":True
                }
            }


        elif uri.startswith("ss://"):

            return parse_ss(uri)


        elif uri.startswith("vmess://"):

            return parse_vmess(uri)


    except Exception:

        return None



def parse_ss(uri):

    try:

        data=uri[5:]

        data=data.split("#")[0]

        raw=base64.urlsafe_b64decode(
            data+"=="
        ).decode()


        method,password,server=raw.split("@")

        host,port=server.split(":")


        return {

            "type":"shadowsocks",

            "tag":"node",

            "server":host,

            "server_port":int(port),

            "method":method,

            "password":password

        }

    except:

        return None



def parse_vmess(uri):

    try:

        data=uri.replace(
            "vmess://",
            ""
        )

        info=json.loads(
            base64.b64decode(data+"==")
        )


        return {

            "type":"vmess",

            "tag":"node",

            "server":info["add"],

            "server_port":int(info["port"]),

            "uuid":info["id"],

            "security":"auto"

        }


    except:

        return None



def make_config(outbound):


    return {

        "log":{
            "level":"error"
        },

        "inbounds":[
            {
                "type":"mixed",
                "listen":"127.0.0.1",
                "listen_port":10808
            }
        ],


        "outbounds":[

            outbound,

            {
                "type":"direct",
                "tag":"direct"
            }

        ]

    }



def test_node(uri):


    outbound=parse_node(uri)


    if not outbound:

        return



    work=tempfile.mkdtemp()


    cfg=make_config(outbound)


    path=os.path.join(
        work,
        "config.json"
    )


    with open(path,"w") as f:

        json.dump(cfg,f)



    try:


        p=subprocess.Popen(

            [
                "./sing-box",
                "run",
                "-c",
                path
            ],

            stdout=subprocess.DEVNULL,

            stderr=subprocess.DEVNULL

        )


        time.sleep(0.8)



        start=time.time()


        r=subprocess.run(

            [
                "curl",

                "-x",
                "socks5h://127.0.0.1:10808",

                "-s",

                "-o",
                "/dev/null",

                "-w",
                "%{http_code}",

                TEST_URL
            ],

            timeout=5,

            capture_output=True

        )


        delay=int(
            (time.time()-start)*1000
        )


        if r.stdout.decode()=="204":


            print(
                "OK",
                delay
            )


            with open(OUTPUT,"a") as f:

                f.write(
                    f"{delay}ms {uri}\n"
                )


    except:

        pass


    finally:

        try:
            p.kill()
        except:
            pass




with open(INPUT,errors="ignore") as f:

    nodes=list(
        set(
            x.strip()
            for x in f.readlines()
        )
    )


# 控制 GitHub Actions 时间

nodes=nodes[:500]


print(
    "开始测速:",
    len(nodes)
)



with concurrent.futures.ThreadPoolExecutor(

    max_workers=30

) as pool:


    list(
        pool.map(
            test_node,
            nodes
        )
    )



print(
    "完成"
)
