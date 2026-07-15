import os
import logging
import base64
import tempfile
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_authenticated_session() -> requests.Session:
    session = requests.Session()
    # 自动获取 GitHub 动作为每个容器自生成的临时安全令牌，赋予 API 访问无限频率
    github_token = os.getenv("GITHUB_TOKEN")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/vnd.github.v3+json'
    }
    if github_token:
        headers['Authorization'] = f'token {github_token}'
        logging.info("已成功自动挂载官方 GITHUB_TOKEN 安全认证凭证")
        
    session.headers.update(headers)
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
    session = create_authenticated_session()
    
    # 走官方标准开放 API (Contents API)
    api_sources = [
        {"url": "https://github.com", "is_b64_file": True},
        {"url": "https://github.com", "is_b64_file": False},
        {"url": "https://github.com", "is_b64_file": False}
    ]
    
    for source in api_sources:
        url = source["url"]
        try:
            logging.info(f"官方 API 通道直连中: {url}")
            response = session.get(url, timeout=(10, 30))
            response.raise_for_status()
            
            data = response.json()
            if "content" in data:
                encoded_content = data["content"].replace("\n", "").replace("\r", "")
                raw_text_bytes = base64.b64decode(encoded_content)
                raw_content = raw_text_bytes.decode('utf-8', errors='ignore').strip()
                
                if source["is_b64_file"] or is_likely_base64(raw_content):
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
                
                logging.info(f"成功通过 API 提取到 {valid_extracted_count} 个最新节点")
        except Exception as e:
            logging.error(f"API 节点调用失败: {url} -> {e}")

    unique_items = list(dict.fromkeys([item.strip() for item in all_extracted_items if item]))
    total_count = len(unique_items)
    
    logging.info(f"聚合完毕，去重后共获得 {total_count} 个真实活节点")
    
    if total_count == 0:
        logging.warning("⚠️ 警告：当前未捕获到任何有效数据，本次跳过更新防止覆盖旧数据。")
        return

    final_nodes = unique_items[:300]
    output_filename = "nodes.txt"
    dir_name = os.path.dirname(os.path.abspath(output_filename))
    
    try:
        with tempfile.NamedTemporaryFile('w', dir=dir_name, delete=False, encoding='utf-8') as temp_file:
            temp_file_path = temp_file.name
            for item in final_nodes:
                temp_file.write(item + "\n")
        os.replace(temp_file_path, output_filename)
        logging.info(f"落盘成功，已生成包含 {len(final_nodes)} 个节点的文件。")
    except IOError as io_err:
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise io_err

if __name__ == "__main__":
    fetch_and_clean_data()
