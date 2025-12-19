import os
import re
import requests
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def get_asset_id_via_api(slug, proxy):
    """
    直接请求 ofiii 的 API 接口获取播放所需的 ID
    """
    # 构造 API 链接 (这是 ofiii 前端获取节目详情的通用接口)
    api_url = f"https://www.ofiii.com/api/v1/channel/watch/{slug}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": f"https://www.ofiii.com/channel/watch/{slug}",
        "Accept": "application/json"
    }
    
    proxies = {"http": proxy, "https": proxy}
    
    try:
        response = requests.get(api_url, headers=headers, proxies=proxies, timeout=15)
        if response.status_code == 200:
            data = response.json()
            # 根据 JSON 结构提取 ID
            # 这里的路径通常是 data -> info -> assetId
            asset_id = data.get('info', {}).get('assetId')
            if asset_id:
                return asset_id
            
            # 备选：如果 JSON 结构不同，尝试在整个 JSON 字符串中找 11 位特征码
            json_str = response.text
            match = re.search(r'["\']assetId["\']\s*:\s*["\']([a-zA-Z0-9_-]{11})["\']', json_str)
            if match:
                return match.group(1)
                
        return None
    except Exception as e:
        logger.error(f"API 请求错误 {slug}: {e}")
        return None

def update_workers_js(results):
    file_path = "workers.js"
    if not os.path.exists(file_path): return
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    count = 0
    for cid, aid in results.items():
        # 匹配 "lhtv01": { ... key: "xxx" } 并替换
        pattern = rf'("{cid}":\s*\{{[^{{}}]+key:\s*")[^"]*"'
        if re.search(pattern, content):
            content = re.sub(pattern, rf'\1{aid}"', content)
            count += 1
            
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"🎉 成功更新 {count} 个频道的 AssetID")

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
    
    proxy = "socks5h://127.0.0.1:10808"
    results = {}

    # 测试代理
    try:
        requests.get("http://ifconfig.me/ip", proxies={"http": proxy, "https": proxy}, timeout=10)
        logger.info("🌍 代理已就绪，开始 API 抓取...")
    except:
        logger.error("❌ 代理连接失败")
        return

    for cid, slug in channels.items():
        logger.info(f"📡 正在调用 API 获取: {cid}...")
        aid = get_asset_id_via_api(slug, proxy)
        if aid:
            logger.info(f"✨ 抓取成功: {aid}")
            results[cid] = aid
        else:
            logger.warning(f"⚠️ 无法从 API 获取 {cid} 的 ID")

    if results:
        update_workers_js(results)

if __name__ == "__main__":
    main()
