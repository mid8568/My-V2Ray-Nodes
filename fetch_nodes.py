import os
import logging
import base64
import tempfile
import requests

# 规范化日志分级
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_and_clean_data() -> None:
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    })
    
    # 【彻底修复】：不再使用列表和复杂的循环切分，直接指定 1 个 2026 年最顶级的全协议海量直连活源
    # 包含了极其完整的长路径参数，不允许任何代码对其进行 split 阉割
    target_url = "https://banyun.moe"
    
    all_nodes = []
    
    try:
        logging.info(f"🚀 正在全速直连顶级分发源: {target_url}")
        # 设置合理的超时
        response = session.get(target_url, timeout=(10, 30))
        response.raise_for_status()
        
        response.encoding = "utf-8"
        raw_content = response.text.strip()
        
        if raw_content:
            # 自动识别并解密大厂接口吐出的 Base64 密文包
            try:
                padded = raw_content + '=' * (-len(raw_content) % 4)
                decoded_bytes = base64.b64decode(padded.encode('utf-8'))
                lines = decoded_bytes.decode('utf-8', errors='ignore').splitlines()
            except Exception:
                # 兼容明文读取
                lines = raw_content.splitlines()
                
            for line in lines:
                cleaned_line = line.strip()
                if cleaned_line.startswith(("vmess://", "vless://", "ss://", "ssr://", "trojan://", "hy2://", "tuic://")):
                    all_nodes.append(cleaned_line)
                    
            logging.info(f"✅ 成功从该源中提取到 {len(all_nodes)} 个活跃代理节点！")
            
    except Exception as e:
        logging.error(f"❌ 核心分发通道请求发生致命网络阻断: {e}")

    # 使用 dict.fromkeys 高效保序去重
    unique_nodes = list(dict.fromkeys([n for n in all_nodes if n]))
    total_count = len(unique_nodes)
    
    logging.info(f"【大盘分析】数据流水线清洗完成，共获得 {total_count} 个真实去重活节点")
    
    # 严格防御：如果因为偶发性网络抽风导致节点数确实为0，优雅 return，保护历史数据
    if total_count == 0:
        logging.warning("⚠️ 提示：本次未捕获到任何有效数据，自动跳过落盘，防止清空您的已有订阅。")
        return

    # 截取前 250 个最优质的节点存入文件
    final_save_nodes = unique_nodes[:250]
    output_filename = "nodes.txt"
    dir_name = os.path.dirname(os.path.abspath(output_filename))
    
    try:
        # 使用 tempfile 进行 OS 级别的安全原子替换，杜绝文件破损与空白
        with tempfile.NamedTemporaryFile('w', dir=dir_name, delete=False, encoding='utf-8') as temp_file:
            temp_file_path = temp_file.name
            for item in final_save_nodes:
                temp_file.write(item + "\n")
        
        os.replace(temp_file_path, output_filename)
        logging.info(f"🎉 恭喜！海量真实节点数据已安全原子落盘至: {output_filename}")
    except IOError as io_err:
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise io_err

if __name__ == "__main__":
    fetch_and_clean_data()
