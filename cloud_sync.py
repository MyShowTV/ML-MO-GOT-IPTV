import os, re, time, requests

def get_asset_id(cid, path):
    url = f"https://www.ofiii.com/{path}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.ofiii.com/"
    }
    # 强制 Python 使用当前环境变量中的代理
    proxies = {
        "http": os.environ.get("HTTP_PROXY"),
        "https": os.environ.get("HTTPS_PROXY")
    }
    
    try:
        # 增加到 20 秒超时，防止 GitHub 网络波动
        res = requests.get(url, headers=headers, proxies=proxies, timeout=20)
        if res.status_code != 200:
            print(f"❌ {cid} 访问失败，状态码: {res.status_code}")
            return None
            
        match = re.search(r"playlist/([a-zA-Z0-9_-]{8,})/master\.m3u8", res.text)
        if match:
            aid = match.group(1)
            print(f"✅ {cid} 抓取成功: {aid}")
            return aid
        else:
            print(f"⚠️ {cid} 页面已打开但未找到钥匙 (可能是代理没到台湾)")
            return None
    except Exception as e:
        print(f"🔥 {cid} 请求发生异常: {str(e)}")
        return None

def sync():
    channels = {
        'lhtv01': 'channel/watch/litv-longturn03',
        'lhtv02': 'channel/watch/litv-longturn05',
        'lhtv03': 'channel/watch/litv-longturn02',
        'lhtv04': 'channel/watch/litv-longturn04',
        'lhtv05': 'channel/watch/litv-longturn01',
        'lhtv06': 'channel/watch/litv-longturn06',
        'lhtv07': 'channel/watch/litv-longturn07',
    }
    
    if not os.path.exists("workers.js"):
        print("❌ 错误：找不到 workers.js 文件")
        return

    with open("workers.js", "r", encoding="utf-8") as f:
        content = f.read()

    success_count = 0
    for cid, path in channels.items():
        aid = get_asset_id(cid, path)
        if aid:
            pattern = rf'("{cid}":\s*\{{[^}}]*key:\s*")([^"]*)(")'
            content = re.sub(pattern, rf'\1{aid}\3', content)
            success_count += 1
        time.sleep(2) # 稍微慢一点，防止被封

    if success_count > 0:
        with open("workers.js", "w", encoding="utf-8") as f:
            f.write(content)
        print(f"🎉 同步完成，共更新 {success_count} 个频道")
    else:
        print("😭 全部失败，请检查代理节点是否可用")
        exit(1) # 强制工作流报错，触发排查日志

if __name__ == "__main__":
    sync()
