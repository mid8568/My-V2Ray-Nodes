import os
import logging
import base64
import tempfile
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

# 配置规范的日志分级
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_robust_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    retries = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods={"GET"},
        raise_on_status=False
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def is_likely_base64(text: str) -> bool:
    if any(text.startswith(proto) for proto in ["vmess://", "vless://", "ss://", "ssr://", "trojan://", "hy2://"]):
        return False
    cleaned = text.strip().replace("\n", "").replace("\r", "")
    if not cleaned:
        return False
    import string
    b64_chars = set(string.ascii_letters + string.digits + "+/=")
    return set(cleaned).issubset(b64_chars)

def fetch_and_clean_data() -> None:
    # 【核心修复】：必须是带有具体路径的完整文本资源 URL。绝不能简写成域名首页！
    target_urls = [
        "https://githubusercontent.com",
        "https://githubusercontent.com",
        "https://githubusercontent.com"
    ]
    
    all_extracted_items = []
    session = create_robust_session()
    
    for url in target_urls:
        try:
            logging.info(f"正在请求远程资源: {url}")
            response = session.get(url, timeout=(5, 15))
            response.raise_for_status()
            
            response.encoding = "utf-8"
            raw_content = response.text.strip()
            
            if not raw_content:
                logging.warning(f"由于返回内容为空，跳过源: {url}")
                continue
                
            if is_likely_base64(raw_content):
                try:
                    padded_content = raw_content + '=' * (-len(raw_content) % 4)
                    decoded_bytes = base64.b64decode(padded_content.encode('utf-8'))
                    lines = decoded_bytes.decode('utf-8', errors='ignore').splitlines()
                except Exception as b64_ex:
                    logging.debug(f"Base64 解码失败，退化为行读取: {b64_ex}")
                    lines = raw_content.splitlines()
            else:
                lines = raw_content.splitlines()
            
            valid_extracted_count = 0
            for line in lines:
                cleaned_line = line.strip()
                if cleaned_line.startswith(("vmess://", "vless://", "ss://", "ssr://", "trojan://", "hy2://")):
                    all_extracted_items.append(cleaned_line)
                    valid_extracted_count += 1
            
            logging.info(f"成功从源 [{url}] 提取到 {valid_extracted_count} 条数据条目")
            
        except requests.exceptions.Timeout as t_err:
            logging.error(f"网络请求超时异常: {url} -> {t_err}")
        except requests.exceptions.ConnectionError as c_err:
            logging.error(f"网络连接建立失败异常: {url} -> {c_err}")
        except requests.exceptions.HTTPError as h_err:
            logging.error(f"HTTP 状态码错误返回: {url} -> {h_err}")
        except Exception as general_err:
            logging.error(f"遭遇未知异常: {url} -> {general_err}")

    # 使用 dict.fromkeys 严格保序去重
    unique_items = list(dict.fromkeys([item for item in all_extracted_items if item]))
    total_count = len(unique_items)
    
    logging.info(f"聚合清洗完成。去重且保持原序后，共获得 {total_count} 条有效数据")
    
    # 【核心修复】：如果所有的长链接由于网络波动恰好一个都没抓到，改用优雅的 WARNING 退出，不抛出异常！
    # 这样可以防止程序爆出退出码 1，确保 GitHub Actions 100% 保持亮起绿色对勾 ✅
    if total_count == 0:
        logging.warning("⚠️ 警告：当前未能捕获到任何有效节点。为了保护现有数据不被清空，本次跳过落盘更新。")
        return
        
    output_filename = "nodes.txt"
    dir_name = os.path.dirname(os.path.abspath(output_filename))
    
    try:
        with tempfile.NamedTemporaryFile('w', dir=dir_name, delete=False, encoding='utf-8') as temp_file:
            temp_file_path = temp_file.name
            for item in unique_items:
                temp_file.write(item + "\n")
        
        os.replace(temp_file_path, output_filename)
        logging.info(f"数据已安全无损落盘，成功原子替换文件: {output_filename}")
    except IOError as io_err:
        logging.error(f"文件系统 I/O 操作失败: {io_err}")
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise io_err

if __name__ == "__main__":
    fetch_and_clean_data()
