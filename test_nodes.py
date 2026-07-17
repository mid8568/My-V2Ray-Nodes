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


INPUT="nodes_all.txt"
OUTPUT="result.txt"

TEST_URL="https://www.gstatic.com/generate_204"


write_lock=threading.Lock()


open(
    OUTPUT,
    "w"
).close()



# =========================
# base64
# =========================


def b64decode(data):

    try:

        return base64.urlsafe_b64decode(
            data+"==="
        ).decode(
            errors="ignore"
        )

    except:

        return ""



# =========================
# VMESS
# =========================


def parse_vmess(uri):

    try:

        raw=uri.replace(
            "vmess://",
            ""
        )


        obj=json.loads(
            b64decode(raw)
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
                    obj.get(
                        "host",
                        obj["add"]
                    )
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

            "server_port":u.port,

            "uuid":u.username,

            "encryption":"none",

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


    except Exception as e:

        print(
            "VLESS error:",
            e
        )

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


        host=u.hostname


        return {


            "type":"trojan",

            "tag":"proxy",

            "server":host,

            "server_port":u.port,

            "password":
            u.username,


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

        data = uri[5:]

        data = data.split("#")[0]


        if "@" not in data:

            return None


        user, host = data.rsplit("@",1)


        try:

            user = base64.urlsafe_b64decode(
                user + "==="
            ).decode()

        except:

            pass


        method,password=user.split(":",1)


        if host.count(":") > 1:

            server = host.rsplit(":",1)[0]

            port = host.rsplit(":",1)[1]

        else:

            server,port=host.split(":",1)


        return {

            "type":"shadowsocks",

            "tag":"proxy",

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


        host=u.hostname


        return {


            "type":"hysteria2",

            "tag":"proxy",

            "server":host,

            "server_port":u.port or 443,

            "password":u.username,


            "tls":{


                "enabled":True,


                "insecure":True,


                "server_name":

                q.get(
                    "sni",
                    [host]
                )[0]


            }

        }


    except:

        return None





# ================= PARSER =================


def parse(uri):


    if uri.startswith("vmess://"):

        return parse_vmess(uri)



    elif uri.startswith("vless://"):

        return parse_vless(uri)



    elif uri.startswith("trojan://"):

        return parse_trojan(uri)



    elif uri.startswith("ss://"):

        return parse_ss(uri)



    elif uri.startswith("hysteria2://"):

        return parse_hy2(uri)



    elif uri.startswith("hy2://"):

        return parse_hy2(
            uri.replace(
                "hy2://",
                "hysteria2://"
            )
        )


    return None






# ================= SING BOX CONFIG =================


def make_config(out):


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


def wait_port():

    import socket


    for i in range(20):

        try:

            s=socket.socket()

            s.connect(
                (
                    "127.0.0.1",
                    PROXY_PORT
                )
            )

            s.close()

            return True


        except:

            time.sleep(0.3)


    return False





def test_node(uri):


    outbound=parse(uri)


    if not outbound:

        return



    cfg=tempfile.mktemp(
        suffix=".json"
    )



    try:


        with open(
            cfg,
            "w"
        ) as f:


            json.dump(
                make_config(outbound),
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


            stderr=subprocess.PIPE

        )



        # 等 sing-box 启动

        if not wait_port():


            p.kill()

            return




        start=time.time()



        r=subprocess.run(


            [

                "curl",


                "-4",


                "--connect-timeout",

                "5",


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


            timeout=12,


            capture_output=True

        )



        delay=int(

            (time.time()-start)

            *1000

        )




        code=r.stdout.decode().strip()



        if code=="204":


            print(

                "OK",

                delay,

                uri[:60]

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


        try:


            if p:

                p.kill()


        except:

            pass



        try:

            os.remove(cfg)

        except:

            pass







# ================= MAIN =================


if not os.path.exists(INPUT):

    print(
        "没有找到节点文件:",
        INPUT
    )

    exit(1)




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



# 测试数量

# GitHub Actions 建议 500-1000

nodes=nodes[:1000]



print(

    "开始测试:",

    len(nodes)

)




with concurrent.futures.ThreadPoolExecutor(

    max_workers=10

) as pool:


    list(

        pool.map(

            test_node,

            nodes

        )

    )




print()

print(

    "测速完成"

)



if os.path.exists(OUTPUT):


    with open(OUTPUT) as f:

        count=len(

            f.readlines()

        )


    print(

        "可用节点:",

        count

    )

else:


    print(

        "可用节点:0"

    )
