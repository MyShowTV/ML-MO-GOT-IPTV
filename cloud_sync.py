import os, re, time, requests

def get_asset_id(cid, slug):
    url = f"https://www.ofiii.com/channel/watch/{slug}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.ofiii.com/",
        "Accept-Language": "zh-TW,zh;q=0.9"
    }
    proxies = { "http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890" }
    
    try:
        res = requests.get(url, headers=headers, proxies=proxies, timeout=15)
        if res.status_code == 200:
            # 策略：直接匹配网页中可能出现的 m3u8 路径指纹
            # 匹配模式：找出 playlist/ 后面的一串字符，直到遇到下一个斜杠
            # 这种方法可以绕过 JSON 的 key 混淆，直接抓取链接片段
            match = re.search(r'playlist/([a-zA-Z0-9_-]+)/', res.text)
            
            # 如果上面没匹配到，尝试匹配 "id":"..." 这种常见的转义格式
            if not match:
                match = re.search(r'["\'](?:assetId|id)["\']\s*[:=]\s*["\']([a-zA-Z0-9_-]+)["\']', res.text)
            
            if match:
                aid = match.group(1)
                print(f"✅ {cid} 抓取成功: {aid}")
                return aid
            else:
                # 打印出网页中 script 标签的一小段内容，帮助我们在日志里定位
                debug_info = re.findall(r'<script.*?>', res.text)
                print(f"⚠️ {cid} 匹配失败。网页包含 {len(debug_info)} 个脚本块。")
        else:
            print(f"❌ {cid} 访问异常: {res.status_code}")
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
    
    if not os.path.exists("workers.js"): return
    with open("workers.js", "r", encoding="utf-8") as f: content = f.read()

    any_updated = False
    for cid, slug in channels.items():
        aid = get_asset_id(cid, slug)
        if aid:
            # 确保正则能匹配到你 workers.js 里的格式
            # 这里匹配类似 "lhtv01": { key: "xxxx" }
            pattern = rf'"{cid}":\s*\{{[^}}]*?key:\s*"[^"]*"'
            replacement = f'"{cid}": {{ name: "", key: "{aid}" }}'
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                any_updated = True
        time.sleep(1)

    if any_updated:
        with open("workers.js", "w", encoding="utf-8") as f: f.write(content)
        print("🚀 恭喜！同步脚本执行成功！")
    else:
        print("😭 脚本未能在 workers.js 中找到对应的 key 字段，请检查文件格式。")

if __name__ == "__main__":
    sync()
