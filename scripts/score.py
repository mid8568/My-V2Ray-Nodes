cat > score.py << 'EOF'

  import sys
  import asyncio
  import re
  import base64
  import time


  PROTOCOL_REGEX = re.compile(
      r'^(vmess|vless|ss|ssr|trojan|hy2|hysteria2|socks|tuic|wireguard)://',
      re.IGNORECASE
    )


  HOST_PORT_REGEX = re.compile(
      r'://[^@]*@?([\w\.\-\[\]:]+):(\d+)'
  )


  def decode_base64_safe(data):
    try:
        cleaned = re.sub(r'[\r\n\t ]', '', data)

        padding = len(cleaned) % 4

        if padding:
            cleaned += '=' * (4 - padding)

        return base64.b64decode(cleaned).decode(
            'utf-8',
            errors='ignore'
        )

    except:
        return ""


  async def test_tcp_node(line, sem):

    async with sem:

        clean_line = line.split('#')[0].strip()

        match = HOST_PORT_REGEX.search(clean_line)

        if not match:
            return (0,9999,line)


        host = match.group(1)
        port = int(match.group(2))


        if host.startswith('[') and host.endswith(']'):
            host = host[1:-1]


        try:

            start = time.perf_counter()


            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host,port),
                timeout=3
            )


            delay=int(
                (time.perf_counter()-start)*1000
            )


            writer.close()

            await writer.wait_closed()


            score=max(
                10,
                min(
                    100,
                    4500//(delay+25)
                )
            )


            return (
                score,
                delay,
                line
            )


        except:

            return (
                0,
                9999,
                line
            )


  async def main():

      with open(
          'temp_all_raw.txt',
          'r',
          encoding='utf-8',
          errors='ignore'
      ) as f:

          raw=f.read()



    if not PROTOCOL_REGEX.search(raw):

        decoded=decode_base64_safe(raw)

        if PROTOCOL_REGEX.search(decoded):

            raw=decoded



    seen=set()

    nodes=[]


    for line in raw.splitlines():

        line=line.strip()


        if not line:
            continue


        if line.startswith('#'):
            continue


        if 'example-node' in line.lower():
            continue


        if 'expired' in line.lower():
            continue


        if not PROTOCOL_REGEX.search(line):
            continue


        key=line.split('#')[0]


        if key not in seen:

            seen.add(key)

            nodes.append(line)



    print(
        "有效节点:",
        len(nodes)
    )



    if len(nodes)==0:

        sys.exit(1)



    sem=asyncio.Semaphore(100)


    tasks=[
        test_tcp_node(n,sem)
        for n in nodes
    ]


    results=await asyncio.gather(*tasks)



    results=[
        x for x in results
        if x[0]>0
    ]



    results.sort(
        key=lambda x:(-x[0],x[1])
    )



    with open(
        'speed_rank.txt',
        'w',
        encoding='utf-8'
    ) as f:

        for score,delay,node in results:

            f.write(
                f"{delay}|{node}\n"
            )



    with open(
        'nodes.txt',
        'w',
        encoding='utf-8'
    ) as f:

        for score,delay,node in results[:300]:

            f.write(
                node+'\n'
            )



    print(
        "测速完成:",
        len(results)
    )



if __name__=="__main__":

    asyncio.run(main())

EOF
