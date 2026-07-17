#!/usr/bin/env python3

import json
import time
import base64
import random
import tempfile
import subprocess
import concurrent.futures
import os
import threading

from urllib.parse import urlparse, parse_qs


INPUT = "nodes_all.txt"
OUTPUT = "result.txt"

# 更适合免费节点
TEST_URL = "https://www.gstatic.com/generate_204"

PROXY_PORT = 10808


write_lock = threading.Lock()


open(OUTPUT, "w").close()



def b64decode(data):

    try:

        return base64.urlsafe_b64decode(
            data + "==="
        ).decode(errors="ignore")

    except:

        return ""



# ================= VMESS =================


def parse_vmess(uri):

    try:

        raw = uri.replace(
            "vmess://",
            ""
        )

        obj=json.loads(
            b64decode(raw)
        )


        server=obj.get(
            "add"
        )


        out={

            "type":"vmess",

            "tag":"node",

            "server":server,

            "server_port":int(
                obj["port"]
            ),

            "uuid":obj["id"],

            "security":obj.get(
                "scy",
                "auto"
            )

        }


        if obj.get("net")=="ws":

            out["transport"]={

                "type":"ws",

                "path":obj.get(
                    "path",
                    "/"
                )

            }



        if obj.get("tls")=="tls":

            out["tls"]={

                "enabled":True,

                "server_name":
                obj.get(
                    "sni",
                    obj.get(
                        "host",
                        server
                    )
                )

            }


        return out


    except:

        return None




# ================= VLESS =================


def parse_vless(uri):

    try:

        u=urlparse(uri)

        q=parse_qs(u.query)

        host=u.hostname

        server=host

        out={
            ...
        }

        host=u.hostname

        server=host

        out={

            "type":"vless",

            "tag":"node",

            "server":server,

            "server_port":u.port,

            "uuid":u.username,

            "packet_encoding":"xudp"
        }

        flow=q.get(
            "flow",
            [""]
        )[0]


        if flow:

            out["flow"]=flow

        security=q.get(
            "security",
            [""]
        )[0]

        if security in (
            "tls",
            "reality"
        ):

          out["tls"]={

                "enabled":True,

                "server_name":
                q.get(
                    "sni",
                    [host]
                )[0]

            }

        if security=="reality":

            out["tls"]["reality"]={

                "enabled":True,

                "public_key":
                q.get(
                    "pbk",
                    [""]
                )[0],

                "short_id":
                q.get(
                    "sid",
                    [""]
                )[0]

            }

        network=q.get(
            "type",
            [""]
        )[0]

        if network=="ws":

            out["transport"]={

                "type":"ws",

                "path":
                q.get(
                    "path",
                    ["/"]
                )[0]

            }

        elif network=="grpc":

            out["transport"]={

                "type":"grpc",

                "service_name":
                q.get(
                    "serviceName",
                    [""]
                )[0]

            }

        return out

    except:

        return None

# ================= TROJAN =================

def parse_trojan(uri):

    try:

        u=urlparse(uri)

        q=parse_qs(
            u.query
        )

        host=u.hostname

        server=host

        return {

            "type":"trojan",

            "tag":"node",

            "server":server,

            "server_port":u.port,

            "password":u.username,

            "tls":{

                "enabled":True,

                "server_name":
                q.get(
                    "sni",
                    [host]
                )[0]

            }


        }


    except:

        return None





# ================= SS =================


def parse_ss(uri):

    try:

        data=uri[5:].split("#")[0]


        if "@" in data:

            user,host=data.rsplit("@",1)

            if ":" not in user:

                user=b64decode(user)

        else:

            return None


        if ":" not in user:
            return None


        method,password=user.split(":",1)


        server,port=host.rsplit(":",1)


        return {

            "type":"shadowsocks",
            "tag":"node",
            "server":server,
            "server_port":int(port),
            "method":method,
            "password":password

        }


    except:

        return None

# ================= HY2 =================


def parse_hy2(uri):

    try:

        u=urlparse(uri)

        q=parse_qs(
            u.query
        )


        return {


            "type":"hysteria2",

            "tag":"node",

            "server":u.hostname,

            "server_port":u.port,

            "password":u.username,


            "tls":{

                "enabled":True,

                "insecure":True,

                "server_name":
                q.get(
                    "sni",
                    [u.hostname]
                )[0]

            }

        }


    except:

        return None





def parse(uri):


    if uri.startswith(
        "vmess://"
    ):

        return parse_vmess(uri)


    if uri.startswith(
        "vless://"
    ):

        return parse_vless(uri)


    if uri.startswith(
        "trojan://"
    ):

        return parse_trojan(uri)


    if uri.startswith(
        "ss://"
    ):

        return parse_ss(uri)


    if uri.startswith(
        "hysteria2://"
    ):

        return parse_hy2(uri)



    return None





# ================= CONFIG =================


def make_config(out):


    out["tag"]="proxy"



    return {


        "log":{

            "level":"error"

        },


        "inbounds":[

            {

                "type":"mixed",

                "listen":"127.0.0.1",

                "listen_port":PROXY_PORT

            }

        ],


        "outbounds":[

            out,

            {

                "type":"direct",

                "tag":"direct"

            }

        ]

    }





# ================= TEST =================


def test_node(uri):


    outbound=parse(uri)


    if not outbound:

        return



    cfg=tempfile.mktemp(
        suffix=".json"
    )



    with open(
        cfg,
        "w"
    ) as f:

        json.dump(
            make_config(outbound),
            f
        )



    p=None


    try:


        p=subprocess.Popen(

            [

                "./sing-box",

                "run",

                "-c",

                cfg

            ],

            stdout=subprocess.DEVNULL,

            stderr=subprocess.PIPE

        )



        time.sleep(3)



        start=time.time()



        r=subprocess.run(

            [

                "curl",

                "-4",

                "-A",

                "Mozilla/5.0",

                "-x",

                f"socks5h://127.0.0.1:{PROXY_PORT}",

                "-s",

                "-o",

                "/dev/null",

                "-w",

                "%{http_code}",

                TEST_URL

            ],

            timeout=10,

            capture_output=True

        )



        delay=int(
            (time.time()-start)*1000
        )



        if r.stdout.decode()=="204" and delay < 3000:


            print(
                "OK",
                delay
            )


            with write_lock:


                with open(
                    OUTPUT,
                    "a"
                ) as f:


                    f.write(
                        f"{delay}ms {uri}\n"
                    )



    except Exception as e:

        pass



    finally:


        if p:

            p.kill()



        try:

            os.remove(cfg)

        except:

            pass





# ================= MAIN =================



with open(
    INPUT,
    errors="ignore"
) as f:


    nodes=list(

        set(

            x.strip()

            for x in f

            if x.strip()

        )

    )



random.shuffle(nodes)



# 测试更多节点

nodes=nodes[:800]


print(
    "开始测试:",
    len(nodes)
)



with concurrent.futures.ThreadPoolExecutor(

    max_workers=25

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
