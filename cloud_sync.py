import os
import re
import json
import requests
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def find_key_in_dict(obj, key_name):
    """
    递归搜索字典，寻找指定的 key。
    应对 Ofiii 页面 JSON 结构变动。
    """
    if isinstance(obj, dict):
        if key_name in obj:
            return obj[key_name]
        for v in obj.values():
            result = find_key_in_dict(v, key_name)
            if result: return result
    elif isinstance(obj, list):
        for item in obj:
            result = find_key_in_dict(item, key_name)
            if result: return result
    return None

def get_asset_id(slug, proxy):
    url = f"https://www.ofiii.com/channel/watch/{slug}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": "https://www.ofiii.com/"
    }
    # 在 Actions 环境中，如果 socks5 不行，可以尝试 http 映射
    proxies = {"http": proxy, "https": proxy}
    
    try:
        response = requests.get(url, headers=headers, proxies=proxies, timeout=15)
        html = response.text
        
        # 方案 A: 深度解析 __NEXT_DATA__
        pattern = r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>'
        match = re.search(pattern, html, re.S)
        if match:
            data = json.loads(match.group(1))
            aid = find_key_in_dict(data, 'assetId')
            if aid and len(str(aid)) == 11:
                return aid
        
        # 方案 B: 正则强搜 (针对你提到的 m3u8 密匙逻辑)
        # 匹配任何在 playlist 路径下的 11 位字符
        raw_match = re.search(r'/playlist/([a-zA-Z0-9_-]{11})/', html)
        if raw_match:
            return raw_match.group(1)

        return None
    except Exception as e:
        logger.error(f"❌ 抓取 {slug} 异常: {e}")
        return None

def update_workers_js(results):
    """
    优化：直接读取模板并替换，或者更新本地 workers.js 文件
    """
    file_path = "workers.js"
    if not os.path.exists(file_path):
        logger.error("未找到 workers.js 文件")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    updated_count = 0
    for cid, aid in results.items():
        # 优化正则：匹配 cid 后面紧跟着的 key 字段
        # 兼容 "lhtv03": { key: "xxxx" } 这种格式
        pattern = rf'("{cid}"\s*:\s*\{{[^{{}}]+key\s*:\s*")[^"]*"'
        if re.search(pattern, content):
            content = re.sub(pattern, rf'\1{aid}"', content)
            updated_count += 1
            
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"💾 同步完成：共更新 {updated_count} 个频道标识")

def main():
    # 你的频道映射表
    channels = {
        'lhtv01': 'litv-longturn01',
        'lhtv02': 'litv-longturn02',
        'lhtv03': 'litv-longturn03',
        'lhtv04': 'litv-longturn11',
        'lhtv05': 'litv-longturn12',
        'lhtv06': 'litv-longturn18',
        'lhtv07': 'litv-longturn21'
    }
    
    # GitHub Actions 配合 Shadowsocks 的默认地址
    proxy = "socks5h://127.0.0.1:10808"
    results = {}

    for cid, slug in channels.items():
        logger.info(f"📡 抓取中: {cid} -> {slug}")
        aid = get_asset_id(slug, proxy)
        if aid:
            logger.info(f"✅ 获取成功: {aid}")
            results[cid] = aid
        else:
            logger.warning(f"⚠️ 频道 {cid} 暂无有效 ID")

    if results:
        update_workers_js(results)
    else:
        logger.error("🚫 未能获取到任何有效数据，停止更新。")

if __name__ == "__main__":
    main()
