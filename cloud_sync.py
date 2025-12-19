import os, re, time, requests, json

def get_asset_id(cid, slug):
    url = f"https://www.ofiii.com/channel/watch/{slug}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.ofiii.com/",
        "Accept-Language": "zh-TW,zh;q=0.9"
    }
    # 走台湾 VPS 代理 (Clash 默认 7890)
    proxies = { "http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890" }
    
    try:
        res = requests.get(url, headers=headers, proxies=proxies, timeout=15)
        if res.status_code == 200:
            # --- 核心改进：万能模糊匹配 ---
            # 1. 尝试从 Next.js 数据块提取 (最准确)
            next_data = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', res.text)
            if next_data:
                # 暴力搜索 JSON 块中的所有 assetId
                ids = re.findall(r'"assetId":"([a-zA-Z0-9_-]+)"', next_data.group(1))
                if ids:
                    print(f"✅ {cid} 抓取成功 (JSON): {ids[0]}")
                    return ids[0]

            # 2. 尝试从链接指纹提取 (你 Network 看到的路径)
            link_id = re.search(r'playlist/([a-zA-Z0-9_-]+)/', res.text)
            if link_id:
                print(f"✅ {cid} 抓取成功 (Link): {link_id.group(1)}")
                return link_id.group(1)

            # 3. 针对 Unicode 转义的暴力提取 (解决“高度混淆”)
            unicode_id = re.search(r'assetId[\\"\s:]+([a-zA-Z0-9_-]+)', res.text)
            if unicode_id:
                print(f"✅ {cid} 抓取成功 (Unicode): {unicode_id.group(1)}")
                return unicode_id.group(1)

            print(f"⚠️ {cid} 匹配失败。源码预览: {res.text[:100]}...")
        else:
            print(f"❌ {cid} 访问失败: {res.status_code}")
    except Exception as e:
        print(f"🔥 {cid} 异常: {str(e)}")
    return None

def sync():
    channels = {
        'lhtv01': 'litv-longturn03',
        'lhtv03': 'litv-longturn02',
        'lhtv05': 'ofiii73',
        'lhtv06': 'ofiii74',
        'lhtv07': 'ofiii76',
    }
    
    file_path = "workers.js"
    if not os.path.exists(file_path):
        print(f"❌ 找不到 {file_path}")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    any_updated = False
    for cid, slug in channels.items():
        aid = get_asset_id(cid, slug)
        if aid:
            # --- 核心改进：松散匹配正则 ---
            # 这个正则可以适配各种引号和空格格式，只要有 cid 和 key 就能替换
            pattern = rf'"{cid}"\s*:\s*\{{[^}}]*?key\s*:\s*["\'][^"\']*["\']'
            replacement = f'"{cid}": {{ name: "", key: "{aid}" }}'
            
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                any_updated = True
            else:
                print(f"❓ {cid} 抓到了 ID 但在 {file_path} 里没找到对应的 key 字段")

    if any_updated:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("🚀 同步成功！")
    else:
        print("😭 未能更新任何数据。请检查 workers.js 是否包含对应的频道 ID。")

if __name__ == "__main__":
    sync()
