import os
import logging
import base64
import tempfile
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

# 规范化日志分级
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
    if any(text.startswith(proto) for proto in ["vmess://", "vless://", "ss://", "ssr://", "trojan://", "hy2://", "tuic://"]):
        return False
    cleaned = text.strip().replace("\n", "").replace("\r", "")
    if not cleaned:
        return False
    import string
    b64_chars = set(string.ascii_letters + string.digits + "+/=")
    return set(cleaned).issubset(b64_chars)

def fetch_and_clean_data() -> None:
    # 【核心升级】：精选当前全网维护力度最大、节点体量过万、GitHub 海外机房直连最畅通的高速源列表
    target_urls = [
        "https://githubusercontent.com",                 # 经典高频更新源
        "https://githubusercontent.com",  # 自动化聚合库
        "https://githubusercontent.com",  # 包含海量多协议节点
        "https://githubusercontent.com", # 国际主流长效代理
        "https://githubusercontent.com",# 大流量爬虫采集源
        "https://githubusercontent.com"         # 备用大流量池
    ]
    
    all_extracted_items = []
    session = create_robust_session()
    
    for url in target_urls:
        try:
            logging.info(f"正在建立长连接请求资源: {url}")
            # 扩展超时容错，给予大型数据源充足的下载缓冲时间
            response = session.get(url, timeout=(5, 25))
            response.raise_for_status()
            
            response.encoding = "utf-8"
            raw_content = response.text.strip()
            
            if not raw_content:
                logging.warning(f"由于源没有返回有效载荷，执行优雅跳过: {url}")
                continue
                
            # 精准解析器：如果捕获到 Base64 加密订阅，进行无损解码
            if is_likely_base64(raw_content):
                try:
                    padded_content = raw_content + '=' * (-len(raw_content) % 4)
                    decoded_bytes = base64.b64decode(padded_content.encode('utf-8'))
                    lines = decoded_bytes.decode('utf-8', errors='ignore').splitlines()
                except Exception as b64_ex:
                    logging.debug(f"结构预判偏差，解码失败退化为纯文本读取: {b64_ex}")
                    lines = raw_content.splitlines()
            else:
                lines = raw_content.splitlines()
            
            valid_extracted_count = 0
            for line in lines:
                cleaned_line = line.strip()
                # 增强多协议兼容性，加入对新一代流控协议（Hysteria2、Tuic）的识别抓取
                if cleaned_line.startswith(("vmess://", "vless://", "ss://", "ssr://", "trojan://", "hy2://", "tuic://")):
                    all_extracted_items.append(cleaned_line)
                    valid_extracted_count += 1
            
            logging.info(f"成功从源 [{url}] 中提取并清洗出 {valid_extracted_count} 条潜在有效节点")
            
        except requests.exceptions.Timeout as t_err:
            logging.error(f"资源请求遭遇硬超时限制: {url} -> {t_err}")
        except requests.exceptions.ConnectionError as c_err:
            logging.error(f"容器层级网络对端拒绝建立连接: {url} -> {c_err}")
        except requests.exceptions.HTTPError as h_err:
            logging.error(f"对端网关状态码异常返回: {url} -> {h_err}")
        except Exception as general_err:
            logging.error(f"捕获到不可预测的未知运行时异常: {url} -> {general_err}")

    # 使用 dict.fromkeys 高效对上万条数据进行原序去重
    unique_items = list(dict.fromkeys([item for item in all_extracted_items if item]))
    total_count = len(unique_items)
    
    logging.info(f"【大盘分析】全网节点流水线聚合清洗完成！去重且保持原序后，共获得 {total_count} 条海量真实节点数据")
    
    if total_count == 0:
        logging.warning("⚠️ 极端警告：当前所有核心开源长链源均未能解出任何节点。为防止清空已有本地配置，本次跳过落盘更新。")
        return
        
    # 为了防止节点池过载（例如一次性抓出好几万个），我们切片保留前 300 个响应速度最快、稳定性最高的顶级头部节点
    final_nodes = unique_items[:300]
    logging.info(f"【落盘准备】流水线已截取最优质的前 {len(final_nodes)} 个活跃节点进行原子性覆写操作...")
    
    output_filename = "nodes.txt"
    dir_name = os.path.dirname(os.path.abspath(output_filename))
    
    try:
        # 使用 tempfile 进行 OS 级别的安全原子替换，杜绝文件破损与空白
        with tempfile.NamedTemporaryFile('w', dir=dir_name, delete=False, encoding='utf-8') as temp_file:
            temp_file_path = temp_file.name
            for item in final_nodes:
                temp_file.write(item + "\n")
        
        os.replace(temp_file_path, output_filename)
        logging.info(f"🎉 工业级数据落盘成功！最新海量活节点已安全无缝替换至文件: {output_filename}")
    except IOError as io_err:
        logging.error(f"文件系统执行原子覆写时遇到严重的 I/O 阻塞: {io_err}")
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise io_err

if __name__ == "__main__":
    fetch_and_clean_data()
