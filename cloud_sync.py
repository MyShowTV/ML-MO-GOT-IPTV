import os
import re
import json
import requests
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def get_asset_id_from_json(slug, proxy):
    """
    通过解析 __NEXT_DATA__ JSON 块提取 AssetID
    """
    url = f"https://www.ofiii.com/channel/watch/{slug}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.ofiii.com/"
    }
    proxies = {"http": proxy, "https": proxy}
    
    try:
        response = requests.get(url, headers=headers, proxies=proxies, timeout=15)
        html = response.text
        
        # 1. 定位 __NEXT_DATA__ 脚本块
        # 这里的 JSON 包含了页面加载所需的所有变量
        pattern = r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>'
        match = re.search(pattern, html, re.S)
        
        if match:
            data = json.loads(match.group(1))
            # 2. 深入 JSON 层级寻找 ID
            # 根据 ofiii 结构，路径通常在 props -> pageProps -> video -> programInfo -> assetId
            # 或者在 props -> pageProps -> channel 内
            page_props = data.get('props', {}).get('pageProps', {})
            
            # 尝试路径 A (频道详情页常用)
            asset_id = page_props.get('video', {}).get('programInfo', {}).get('assetId')
            
            # 尝试路径 B (备选)
            if not asset_id:
                asset_id = page_props.get('assetId')
            
            if asset_id:
                return asset_id
        
        # 3. 兜底方案：如果在 JSON 对象里没找到，直接在整段 JSON 字符串里强搜 11 位特征码
        # 寻找 assetId":"XXXXXXXXXXX"
        raw_match = re.search(r'assetId["\']\s*:\s*["\']([a-zA-Z0-9_-]{11})["\']', html)
        if raw_match:
            return raw_match.group(1)

        return None
    except Exception as e:
        logger.error(f"提取 {slug} 失败: {e}")
        return None

def update_workers_js(results):
    file_path = "workers.js"
    if not os.path.exists(file_path): return
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    count = 0
    for cid, aid in results.items():
        # 精准匹配 JSON 结构中的 key 字段
        pattern = rf'("{cid}":\s*\{{[^{{}}]+key:\s*")[^"]*"'
        if re.search(pattern, content):
            content = re.sub(pattern, rf'\1{aid}"', content)
            count += 1
            
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"✅ 同步成功！已更新 {count} 个频道。")

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
    
    # 注意：在 Actions 里，你的配置启动了 ss-local 监听 10808
    proxy = "socks5h://127.0.0.1:10808"
    results = {}

    for cid, slug in channels.items():
        logger.info(f"🔍 正在同步: {cid} ({slug})")
        aid = get_asset_id_from_json(slug, proxy)
        if aid:
            logger.info(f"✨ 成功匹配 ID: {aid}")
            results[cid] = aid
        else:
            logger.warning(f"❌ 频道 {cid} 抓取不到 ID")

    if results:
        update_workers_js(results)

if __name__ == "__main__":
    main()
