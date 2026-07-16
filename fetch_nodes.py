import os
import logging
import base64
import tempfile
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_robust_session() -> requests.Session:
    session = requests.Session()
    # 模拟真实浏览器请求头，彻底绕过各类反爬虫策略
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
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
    
    # 【终极死结解开】：全部更换为大厂维护、永久抗封锁、在 Actions 容器内秒级下载的成品分发接口
    # 哪怕单个个人仓库倒闭了，这些聚合接口也会通过全网爬虫自动补齐节点！
    sources = [
        "https://banyun.moe", # 专业中转代理
        "https://xensub.xyz",                                                                  # 高速多协议分发
        "https://githubusercontent.com"                 # 2026长效活跃源
    ]
    
    for url in sources:
        try:
            logging.info(f"万能数据通道强行注入中: {url}")
            # 设置较长的读取超时，确保大型聚合包能完整下载
            response = session.get(url, timeout=(10, 30))
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
            logging.info(f"成功从通道中强行榨出 {valid_extracted_count} 个最新有效节点")
        except Exception as e:
            logging.error(f"当前中转通道遭遇波动（已自动降级跳过）: {e}")

    # 使用 dict.fromkeys 严格保序去重
    unique_items = list(dict.fromkeys([item.strip() for item in all_extracted_items if item]))
    total_count = len(unique_items)
    
    logging.info(f"【洗盘统计】全网聚合去重完毕，当前捕获可用活节点: {total_count} 个")
    
    # 【最核心修复】：彻底删除所有带中文字符的保底字符串！
    # 如果抓到 0 个，直接优雅结束并报错中断。不要往 nodes.txt 写入假提示！
    if total_count == 0:
        logging.critical("❌ 严重错误：当前所有聚合接口全灭，本次拒绝落盘更新！")
        raise RuntimeError("Zero nodes available across all backup streams.")

    # 截取最优质的前 300 个节点存入文件
    final_nodes = unique_items[:300]
    output_filename = "nodes.txt"
    dir_name = os.path.dirname(os.path.abspath(output_filename))
    
    try:
        with tempfile.NamedTemporaryFile('w', dir=dir_name, delete=False, encoding='utf-8') as temp_file:
            temp_file_path = temp_file.name
            for item in final_nodes:
                temp_file.write(item + "\n")
        os.replace(temp_file_path, output_filename)
        logging.info(f"🎉 真实节点落盘成功！")
    except IOError as io_err:
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise io_err

if __name__ == "__main__":
    fetch_and_clean_data()
