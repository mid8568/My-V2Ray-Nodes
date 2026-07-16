import base64
import json
import urllib.parse
import subprocess
import tempfile
import requests
import time
import os


def parse_node(uri):

    uri = uri.strip()


    # =====================
    # VLESS
    # =====================

    if uri.startswith("vless://"):

        u = urllib.parse.urlparse(uri)

        query = urllib.parse.parse_qs(u.query)


        host = query.get("host", [""])[0]
        sni = query.get("sni", [u.hostname])[0]
        path = query.get("path", [""])[0]


        if query.get("type", [""])[0] == "ws":

            if not host or not sni or not path:
                return None



        return {

            "type": "vless",

            "tag": "node",

            "server": u.hostname,

            "server_port": u.port,

            "uuid": u.username,


            "flow":
                query.get("flow", [""])[0],


            "tls": {

                "enabled":
                    query.get("security", [""])[0] == "tls",


                "server_name":
                    sni,


                "utls": {

                    "enabled": True,

                    "fingerprint":
                        query.get("fp",
                        ["chrome"])[0]

                }

            },


            "transport": {

                "type":
                    query.get("type",
                    ["tcp"])[0],


                "path":
                    urllib.parse.unquote(path),


                "headers": {

                    "Host": host

                }

            }

        }



    # =====================
    # Trojan
    # =====================

    if uri.startswith("trojan://"):


        u = urllib.parse.urlparse(uri)


        query = urllib.parse.parse_qs(u.query)


        return {

            "type":"trojan",

            "tag":"node",

            "server":u.hostname,

            "server_port":u.port,

            "password":u.username,


            "tls":{

                "enabled":True,

                "server_name":
                query.get("sni",
                [u.hostname])[0]

            }

        }



    # =====================
    # Shadowsocks
    # =====================

    if uri.startswith("ss://"):

        try:

            raw=uri[5:].split("#")[0]


            data=base64.urlsafe_b64decode(
                raw+"=="
            ).decode()


            method,password_host=data.split("@")

            method,password=method.split(":")

            host,port=password_host.split(":")


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



    return None





def test_proxy(node):


    try:


        config=parse_node(node)
        
        if not config:
            return None


        import random

        port=random.randint(20000,30000)



        singbox_config={


            "log":{

                "level":"error"

            },


            "inbounds":[

                {

                    "type":"socks",

                    "listen":"127.0.0.1",

                    "listen_port":port

                }

            ],


            "outbounds":[

                config

            ]

        }



        with tempfile.NamedTemporaryFile(

            mode="w",

            suffix=".json",

            delete=False

        ) as f:


            json.dump(

                singbox_config,

                f

            )


            filename=f.name
            

        process=subprocess.Popen(

            [

                "sing-box",

                "run",

                "-c",

                filename

            ],

            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE

        )



        time.sleep(2)
        
        if process.poll() is not None:
            
           err=process.stderr.read().decode()
            
           print(err[:500])
            
           process.kill()
            
           return None


        start=time.time()



        r=requests.get(

            "https://www.gstatic.com/generate_204",

            proxies={


                "http":

                f"socks5h://127.0.0.1:{port}",


                "https":

                f"socks5h://127.0.0.1:{port}"


            },

            timeout=5

        )



        delay=int(

            (time.time()-start)*1000

        )


        process.kill()

        os.remove(filename)



        if r.status_code in [200,204]:

            return delay



except Exception as e:

    print("测速错误:",e)

    return None






input_file="clean_nodes.txt"

output_file="speed_rank.txt"



results=[]



with open(

    input_file,

    "r",

    encoding="utf-8"

) as f:


    for line in f:


        node=line.strip()


        if not node:

            continue



        print(

            "测试:",

            node[:60]

        )



        delay=test_proxy(node)



        if delay:


            print(

                "成功",

                delay,

                "ms"

            )


            results.append(

                f"{delay}|{node}"

            )


        else:


            print(

                "失败"

            )





results.sort(

    key=lambda x:int(
        x.split("|")[0]
    )

)



with open(

    output_file,

    "w",

    encoding="utf-8"

) as f:


    for item in results:

        f.write(item+"\n")



print("================")

print(

    "生成 speed_rank.txt"

)


print(

    "有效节点:",

    len(results)

)
