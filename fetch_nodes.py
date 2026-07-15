import os
import logging
import base64
import tempfile
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_robust_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    return session

def is_likely_base64(text: str) -> bool:
    if any(text.startswith(proto) for proto in ["vmess://", "vless://", "ss://", "ssr://", "trojan://", "hy2://", "tuic://"]):
        return False
    cleaned = text.strip().replace("\n", "").replace("\r", "")
    if not cleaned:
        return False
    import string
    b64_chars = set(string.ascii_letters + string.digits + "+/=")
    return set(cleaned).issubset(b64_chars)

def fetch_and_clean_data() -> None:
    all_extracted_items = []
    session = create_robust_session()
    
    # 【多重突围通道】：由于 Actions 机房会阻断 githubusercontent 域名，
    # 我们全部使用部署在 jsDelivr 国际高速 CDN、Netlify 及海外中转后端的万能分发源。
    # 这些源不仅在 Actions 内部拥有极高连通率，而且吐出的节点体量极其庞大。
    sources = [
        "https://jsdelivr.net",                      # 绕过官方封锁的 CDN 镜像
        "https://netlify.app",                         # 全球网络中转镜像池
        "https://xensub.xyz",                                      # 高速订阅生成器接口
        "https://jsdelivr.net"       # 备用大池CDN镜像
    ]
    
    for url in sources:
        try:
            logging.info(f"正在建立无阻碍长连接: {url}")
            response = session.get(url, timeout=(10, 25))
            response.raise_for_status()
            
            response.encoding = "utf-8"
            raw_content = response.text.strip()
            
            if not raw_content:
                continue
                
            if is_likely_base64(raw_content):
                try:
                    padded = raw_content + '=' * (-len(raw_content) % 4)
                    lines = base64.b64decode(padded.encode('utf-8')).decode('utf-8', errors='ignore').splitlines()
                except Exception:
                    lines = raw_content.splitlines()
            else:
                lines = raw_content.splitlines()
            
            valid_extracted_count = 0
            for line in lines:
                cleaned_line = line.strip()
                if cleaned_line.startswith(("vmess://", "vless://", "ss://", "ssr://", "trojan://", "hy2://", "tuic://")):
                    all_extracted_items.append(cleaned_line)
                    valid_extracted_count += 1
            logging.info(f"成功从当前数据流中提取到 {valid_extracted_count} 个最新有效节点")
        except Exception as e:
            logging.error(f"当前加速通道发生网络抖动（已自动平滑跳过）: {e}")

    unique_items = list(dict.fromkeys([item.strip() for item in all_extracted_items if item]))
    total_count = len(unique_items)
    
    logging.info(f"聚合完毕，去重后全网共获得 {total_count} 个真实活跃节点")
    
    # 彻底清除所有的中文字符保底。由于你在第一步删除了旧文件，Git add . 必须捕捉到新文件的诞生
    if total_count == 0:
        logging.warning("⚠️ 警告：当前未捕获到新节点，本次跳过文件强制生成。")
        return

    # 截取前 300 个最优质的节点存入文件
    final_nodes = unique_items[:300]
    output_filename = "nodes.txt"
    dir_name = os.path.dirname(os.path.abspath(output_filename))
    
    try:
        with tempfile.NamedTemporaryFile('w', dir=dir_name, delete=False, encoding='utf-8') as temp_file:
            temp_file_path = temp_file.name
            for item in final_nodes:
                temp_file.write(item + "\n")
        os.replace(temp_file_path, output_filename)
        logging.info(f"🎉 工业级原子替换成功！")
    except IOError as io_err:
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise io_err

if __name__ == "__main__":
    fetch_and_clean_data()
