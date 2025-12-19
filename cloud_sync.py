import os
import re
import requests
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def get_asset_id_final(slug, proxy):
    url = f"https://www.ofiii.com/channel/watch/{slug}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.ofiii.com/"
    }
    proxies = {"http": proxy, "https": proxy}
    
    try:
        response = requests.get(url, headers=headers, proxies=proxies, timeout=15)
        html = response.text
        
        # 1. 寻找 window.__PRELOADED_STATE__ 块中的 assetId
        # 匹配 assetId":"XXXXXXXXXXX" 格式
        match = re.search(r'assetId["\']\s*:\s*["\']([a-zA-Z0-9_-]{11})["\']', html)
        if match:
            return match.group(1)
        
        # 2. 如果失败，寻找 URL 特征 (你之前提供的 PKIOGb6cWYI 这种)
        # 即使它没在源码显示，有时也会出现在 prefetch 链接里
        match_url = re.search(r'/([a-zA-Z0-9_-]{11})/master\.m3u8', html)
        if match_url:
            return match_url.group(1)

        # 3. 实在不行，打印一小段源码看看是不是被封 IP 了
        if "抱歉，您所在的地區無法收看" in html:
            logger.error(f"❌ 地区限制！VPS IP {proxy} 被识别为非台湾地区")
        
        return None
    except Exception as e:
        logger.error(f"请求出错: {e}")
        return None

def update_workers_js(results):
    file_path = "workers.js"
    if not os.path.exists(file_path): return
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    count = 0
    for cid, aid in results.items():
        # 这里用一种更暴力的替换方式，直接找关键字
        pattern = rf'"{cid}":\s*\{{[^{{}}]+key:\s*".*?"'
        replacement = f'"{cid}": {{ name: "龙华频道", key: "{aid}"'
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            count += 1
            
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"✅ 同步完成，更新了 {count} 个 ID")

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
    
    # 使用 socks5h 确保 DNS 也在 VPS 上解析
    proxy = "socks5h://127.0.0.1:10808"
    results = {}

    try:
        ip = requests.get("http://ifconfig.me/ip", proxies={"http": proxy, "https": proxy}, timeout=10).text.strip()
        logger.info(f"🌍 出口 IP 确认: {ip}")
    except:
        logger.error("❌ 代理连接断开")
        return

    for cid, slug in channels.items():
        logger.info(f"🔍 正在检索: {cid}...")
        aid = get_asset_id_final(slug, proxy)
        if aid:
            logger.info(f"✨ 发现 ID: {aid}")
            results[cid] = aid
        else:
            logger.warning(f"❌ {cid} 依然没拿到 ID")

    if results:
        update_workers_js(results)

if __name__ == "__main__":
    main()
