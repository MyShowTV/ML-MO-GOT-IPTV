import os, re, time, requests, json

def get_asset_id(cid, slug):
    url = f"https://www.ofiii.com/channel/watch/{slug}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.ofiii.com/",
        "Accept-Language": "zh-TW,zh;q=0.9"
    }
    # 走台湾 VPS 代理
    proxies = { "http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890" }
    
    try:
        res = requests.get(url, headers=headers, proxies=proxies, timeout=15)
        if res.status_code == 200:
            # 方案 A：针对 Next.js 框架，从数据脚本块中剥离 JSON
            data_script = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', res.text)
            if data_script:
                raw_json = data_script.group(1)
                # 暴力搜索 json 中所有的 assetId 字段
                asset_matches = re.findall(r'"assetId":"([a-zA-Z0-9_-]+)"', raw_json)
                if asset_matches:
                    # 通常第一个就是我们需要的频道 ID
                    aid = asset_matches[0]
                    print(f"✅ {cid} 抓取成功 (JSON): {aid}")
                    return aid

            # 方案 B：如果 A 失败，尝试搜索你 Network 里看到的 playlist 链接模式
            regex_match = re.search(r'playlist/([a-zA-Z0-9_-]+)/', res.text)
            if regex_match:
                aid = regex_match.group(1)
                print(f"✅ {cid} 抓取成功 (Regex): {aid}")
                return aid
                
            print(f"⚠️ {cid} 网页已打开，但 ID 被高度混淆")
        else:
            print(f"❌ {cid} 访问失败: {res.status_code}")
    except Exception as e:
        print(f"🔥 {cid} 网络异常: {str(e)}")
    return None

def sync():
    channels = {
        'lhtv01': 'litv-longturn03',
        'lhtv03': 'litv-longturn02',
        'lhtv05': 'ofiii73',
        'lhtv06': 'ofiii74',
        'lhtv07': 'ofiii76',
    }
    
    if not os.path.exists("workers.js"): return
    with open("workers.js", "r", encoding="utf-8") as f: content = f.read()

    any_updated = False
    for cid, slug in channels.items():
        aid = get_asset_id(cid, slug)
        if aid:
            # 匹配 workers.js 里的 "lhtv01": { ... key: "..." } 并替换
            pattern = rf'"{cid}":\s*\{{[^}}]*?key:\s*"[^"]*"'
            replacement = f'"{cid}": {{ name: "", key: "{aid}" }}'
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                any_updated = True
        time.sleep(1)

    if any_updated:
        with open("workers.js", "w", encoding="utf-8") as f: f.write(content)
        print("🚀 同步任务圆满完成！")
    else:
        print("😭 依然未能自动抓取，请手动检查代码或 workers.js 格式。")

if __name__ == "__main__":
    sync()
