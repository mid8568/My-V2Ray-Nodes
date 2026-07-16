import base64
import json
import urllib.parse
import uuid


def parse_node(uri):

    uri = uri.strip()


    # VLESS
    if uri.startswith("vless://"):

        u = urllib.parse.urlparse(uri)

        query = urllib.parse.parse_qs(u.query)

        return {

            "type":"vless",

            "tag":"node",

            "server":u.hostname,

            "server_port":u.port,

            "uuid":u.username,

            "flow":
            query.get("flow",[""])[0],

            "tls":
            {
                "enabled":
                query.get("security",[""])[0]=="tls"
            }

        }


    # Trojan

    if uri.startswith("trojan://"):

        u=urllib.parse.urlparse(uri)


        return {

            "type":"trojan",

            "tag":"node",

            "server":u.hostname,

            "server_port":u.port,

            "password":u.username

        }


    # Shadowsocks

    if uri.startswith("ss://"):

        raw=uri[5:].split("#")[0]


        try:

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
import time


input_file = "tcp_alive_nodes.txt"
output_file = "speed_rank.txt"


results = []


with open(input_file,"r",encoding="utf-8") as f:

    for line in f:

        node=line.strip()

        if not node:
            continue


        # 这里暂时使用TCP延迟
        delay=100


        results.append(
            f"{delay}|{node}"
        )



# 延迟排序
results.sort(
    key=lambda x:int(x.split("|")[0])
)



with open(output_file,"w",encoding="utf-8") as f:

    for item in results:

        f.write(item+"\n")



print("生成 speed_rank.txt")
print("节点数量:",len(results))
