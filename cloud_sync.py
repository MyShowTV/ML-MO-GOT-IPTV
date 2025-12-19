import os
import re
import requests
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def get_asset_id(slug, proxy):
    """
    通过模拟 API 请求直接获取 AssetID
    """
    url = f"https://www.ofiii.com/channel/watch/{slug}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": "https://www.ofiii.com/"
    }
    proxies = {
        "http": proxy,
        "https": proxy
    }
    
    try:
        # 1. 获取网页源码
        response = requests.get(url, headers=headers, proxies=proxies, timeout=15)
        html = response.text
        
        # 2. 搜索 AssetID 的几种可能模式
        # 模式 A: 搜索 11 位字符特征 (如 PKIOGb6cWYI)
        # 这种 ID 通常出现在 playlist 链接中
        match_url = re.search(r'video/playlist/([a-zA-Z0-9_-]{11})/', html)
        if match_url:
            return match_url.group(1)
            
        # 模式 B: 搜索 JSON 数据中的 assetId
        match_json = re.search(r'["\']assetId["\']\s*[:=]\s*["\']([^"\']{10,12})["\']', html)
        if match_json:
            return match_json.group(1)
            
        return None
    except Exception as e:
        logger.error(f"请求 {slug} 出错: {e}")
        return None

def update_workers_js(results):
    file_path = "workers.js"
    if not os.path.exists(file_path): return
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    count = 0
    for cid, aid in results.items():
        pattern = rf'("{cid}":\s*\{{[^{{}}]+key:\s*")[^"]*"'
        if re.search(pattern, content):
            content = re.sub(pattern, rf'\1{aid}"', content)
            count += 1
            
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"✅ 成功更新 {count} 个频道")

def main():
    channels = {
        'lhtv01': 'litv-longturn01',
        'lhtv02': 'litv-longturn02',
        'lhtv03': 'litv-longturn03',
        'lhtv04': 'litv-longturn11',
        'lhtv05': 'litv-longturn12',
        'lhtv06': 'litv-longturn18',
        'lhtv07': 'litv-longturn21'
    }
    
    # Shadowsocks 本地代理地址
    proxy = "socks5h://127.0.0.1:10808"
    results = {}

    # 先测试代理是否通畅
    try:
        test_ip = requests.get("http://ifconfig.me/ip", proxies={"http": proxy, "https": proxy}, timeout=10).text
        logger.info(f"🌍 代理出口 IP: {test_ip.strip()}")
    except:
        logger.error("❌ 代理无法连接，请检查 Shadowsocks 设置")
        return

    for cid, slug in channels.items():
        logger.info(f"🔍 正在检索: {cid}...")
        aid = get_asset_id(slug, proxy)
        if aid:
            logger.info(f"✨ 发现 ID: {aid}")
            results[cid] = aid
        else:
            logger.warning(f"⚠️ 频道 {cid} 提取失败")

    if results:
        update_workers_js(results)

if __name__ == "__main__":
    main()
