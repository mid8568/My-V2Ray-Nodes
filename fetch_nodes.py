import os
import logging
import base64
import tempfile
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

# 1. 规范的日志分级配置（移除全局硬编码，适配标准流水线输出）
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_robust_session() -> requests.Session:
    """
    建立高容错性的网络请求 Session。
    3. 优化点：引入较新版 urllib3 推荐的 allowed_methods，显式限缩仅对安全幂等的 GET 请求进行重试。
    """
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    
    retries = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods={"GET"},  # 显式限制重试方法，避免对非幂等请求造成网络副作用
        raise_on_status=False
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def is_likely_base64(text: str) -> bool:
    """
    2. 优化点：基于启发式特征过滤进行预判，避免盲目将普通明文文本丢进 Base64 解码器中引发性能或逻辑开销。
    标准 V2Ray 订阅明文开头通常包含协议特征串，而密文明文特征泾渭分明。
    """
    # 如果文本本身就包含明显的协议特征头，必然不是纯 Base64 订阅密文
    if any(text.startswith(proto) for proto in ["vmess://", "vless://", "ss://", "ssr://", "trojan://"]):
        return False
    
    # 过滤非 Base64 字符集及长度非法的情况（Base64 长度通常是 4 的倍数，去掉填充符后也是如此）
    cleaned = text.strip().replace("\n", "").replace("\r", "")
    if not cleaned:
        return False
        
    import string
    b64_chars = set(string.ascii_letters + string.digits + "+/=")
    return set(cleaned).issubset(b64_chars)

def fetch_and_clean_data() -> None:
    target_urls = [
        "https://v1.mk",
        "https://banyun.moe",
        "https://githubusercontent.com"
    ]
    
    all_extracted_items = []
    session = create_robust_session()
    
    for url in target_urls:
        try:
            # 5. 日志分级：正常请求使用 INFO
            logging.info(f"正在请求远程资源: {url}")
            response = session.get(url, timeout=(5, 15))
            response.raise_for_status()
            
            # 1. 优化点：修正 apparent_encoding 自主猜测的不可靠性。目标接口为标准 API 或 GitHub 纯文本资源，明确强制指定 UTF-8 确保最高稳定性
            response.encoding = "utf-8"
            raw_content = response.text.strip()
            
            # 5. 日志分级：数据为空时属于潜在风险，触发 WARNING
            if not raw_content:
                logging.warning(f"由于返回内容为空，跳过源: {url}")
                continue
                
            # 2. 优化点：先过筛，再解码
            if is_likely_base64(raw_content):
                try:
                    padded_content = raw_content + '=' * (-len(raw_content) % 4)
                    decoded_bytes = base64.b64decode(padded_content.encode('utf-8'))
                    lines = decoded_bytes.decode('utf-8', errors='ignore').splitlines()
                except (ValueError, TypeError, base64.binascii.Error) as b64_ex:
                    logging.debug(f"结构预判误报，Base64 解码失败，退化为行读取: {b64_ex}")
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
            
        # 5. 日志分级：网络层级发生的错误属于突发故障，统一触发 ERROR 并打印详细上下游堆栈
        except requests.exceptions.Timeout as t_err:
            logging.error(f"网络请求超时异常: {url} -> {t_err}")
        except requests.exceptions.ConnectionError as c_err:
            logging.error(f"网络连接建立失败异常: {url} -> {c_err}")
        except requests.exceptions.HTTPError as h_err:
            logging.error(f"HTTP 状态码错误返回 ({response.status_code}): {url} -> {h_err}")
        except Exception as general_err:
            logging.error(f"遭遇不可预期的未知运行时异常: {url} -> {general_err}")

    # 使用 dict.fromkeys 严格保序去重
    unique_items = list(dict.fromkeys([item for item in all_extracted_items if item]))
    total_count = len(unique_items)
    
    # 5. 日志分级：最终汇总属于核心全局状态，使用 INFO
    logging.info(f"聚合清洗完成。去重且保持原序后，共获得 {total_count} 条有效数据")
    
    if total_count == 0:
        logging.critical("所有配置的数据源均无法获取任何有效文本。程序被迫中断。")
        raise RuntimeError("Data collection failed completely.")
        
    # 4. 优化点：基于原子操作的文件持久化方案。先安全写入操作系统临时区，随后无缝原子替换目标文件，防止进程中途被内核 Kill 产生坏死碎片文件。
    output_filename = "nodes.txt"
    dir_name = os.path.dirname(os.path.abspath(output_filename))
    
    try:
        # 使用 tempfile.NamedTemporaryFile 并指定相同的存储介质目录，确保 os.replace 处于同分区内能实现真正的原子指针替换
        with tempfile.NamedTemporaryFile('w', dir=dir_name, delete=False, encoding='utf-8') as temp_file:
            temp_file_path = temp_file.name
            for item in unique_items:
                temp_file.write(item + "\n")
        
        # 核心步骤：原子性覆写
        os.replace(temp_file_path, output_filename)
        logging.info(f"数据已安全无损落盘，成功原子替换文件: {output_filename}")
    except IOError as io_err:
        logging.error(f"文件系统 I/O 操作失败: {io_err}")
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise io_err

if __name__ == "__main__":
    fetch_and_clean_data()
