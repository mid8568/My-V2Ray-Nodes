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
import socket

from urllib.parse import urlparse, parse_qs


INPUT="nodes_all.txt"

OUTPUT="result.txt"


TEST_URL="https://www.gstatic.com/generate_204"


MAX_WORKERS=30


write_lock=threading.Lock()



open(
    OUTPUT,
    "w"
).close()



# =========================
# TCP检测
# =========================


def tcp_check(host,port):

    try:

        s=socket.socket()

        s.settimeout(2)

        s.connect(
            (
                host,
                port
            )
        )

        s.close()

        return True


    except:

        return False





# =========================
# VMESS
# =========================


def parse_vmess(uri):

    try:

        raw=uri.replace(
            "vmess://",
            ""
        )


        raw += "=" * (
            4-len(raw)%4
        )


        obj=json.loads(

            base64.b64decode(
                raw
            ).decode()

        )


        out={


            "type":"vmess",

            "tag":"proxy",

            "server":
            obj["add"],


            "server_port":
            int(obj["port"]),


            "uuid":
            obj["id"],


            "security":
            obj.get(
                "scy",
                "auto"
            )

        }



        if obj.get("net")=="ws":

            out["transport"]={

                "type":"ws",

                "path":
                obj.get(
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
                    obj["add"]
                )

            }



        return out


    except:

        return None





# =========================
# VLESS
# =========================


def parse_vless(uri):

    try:

        u=urlparse(uri)

        q=parse_qs(
            u.query
        )


        host=u.hostname


        if not host:

            return None



        out={


            "type":"vless",

            "tag":"proxy",

            "server":host,

            "server_port":
            u.port,


            "uuid":
            u.username,


            "encryption":
            "none"


        }



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


            pbk=q.get(
                "pbk",
                [""]
            )[0]

            if not pbk:

                return None



            out["tls"]["reality"]={

                "enabled":True,

                "public_key":pbk,

                "short_id":
                q.get(
                    "sid",
                    [""]
                )[0]

            }



            out["tls"]["utls"]={

                "enabled":True,

                "fingerprint":
                q.get(
                    "fp",
                    ["chrome"]
                )[0]

            }




        net=q.get(
            "type",
            [""]
        )[0]



        if net=="ws":


            out["transport"]={

                "type":"ws",

                "path":
                q.get(
                    "path",
                    ["/"]
                )[0]

            }



        elif net=="grpc":


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





# =========================
# TROJAN
# =========================


def parse_trojan(uri):

    try:


        u=urlparse(uri)

        q=parse_qs(
            u.query
        )


        return {


            "type":"trojan",

            "tag":"proxy",

            "server":
            u.hostname,


            "server_port":
            u.port,


            "password":
            u.username,


            "tls":{

                "enabled":True,

                "server_name":
                q.get(
                    "sni",
                    [u.hostname]
                )[0]

            }

        }


    except:

        return None





# =========================
# parser
# =========================


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


    return None





# =========================
# sing-box config
# =========================


def make_config(out,port):


    return {


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

            out

        ]

    }





def wait_port(port):


    for i in range(30):

        if tcp_check(
            "127.0.0.1",
            port
        ):

            return True


        time.sleep(
            0.2
        )


    return False





# =========================
# test
# =========================


def test_node(uri):


    out=parse(uri)


    if not out:

        return



    if not tcp_check(
        out["server"],
        out["server_port"]
    ):

        return



    port=random.randint(
        20000,
        50000
    )



    cfg=tempfile.mktemp(
        suffix=".json"
    )



    p=None


    try:


        with open(
            cfg,
            "w"
        ) as f:


            json.dump(
                make_config(
                    out,
                    port
                ),
                f
            )



        p=subprocess.Popen(

            [

                "./sing-box",

                "run",

                "-c",

                cfg

            ],

            stdout=subprocess.DEVNULL,

            stderr=subprocess.DEVNULL

        )



        if not wait_port(port):

            return




        start=time.time()



        r=subprocess.run(

            [

                "curl",

                "-x",

                f"socks5h://127.0.0.1:{port}",

                "-m",

                "10",

                "-s",

                "-o",

                "/dev/null",

                "-w",

                "%{{http_code}}",

                TEST_URL

            ],

            capture_output=True,

            timeout=15

        )



        delay=int(

            (time.time()-start)*1000

        )



        code=r.stdout.decode().strip()



        if code in (

            "200",

            "204"

        ):


            print(
                "OK",
                delay,
                uri[:50]
            )



            with write_lock:


                with open(
                    OUTPUT,
                    "a"
                ) as f:


                    f.write(

                        f"{delay}ms {uri}\n"

                    )




    except:

        pass



    finally:


        if p:

            try:

                p.kill()

            except:

                pass



        try:

            os.remove(cfg)

        except:

            pass





# =========================
# main
# =========================


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



print(
    "节点:",
    len(nodes)
)



random.shuffle(nodes)



with concurrent.futures.ThreadPoolExecutor(

    max_workers=MAX_WORKERS

) as pool:


    list(
        pool.map(
            test_node,
            nodes
        )
    )



print(
    "测速完成"
)
