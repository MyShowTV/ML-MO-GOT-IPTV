import os, re, time, requests

def get_asset_id(cid, slug):
    print(f"🔍 正在处理频道: {cid}...")
    
    # --- 这里是你的准确信息 ---
    # 记得在用户名后面加上 -country-tw 确保是台湾 IP
    user = "brd-customer-hl_739668d7-zone-unblocker_ofiii-country-tw"
    password = "zcg6zr5vi8qi"
    proxy_url = f"http://{user}:{password}@brd.superproxy.io:33335"
    
    proxies = {
        "http": proxy_url,
        "https": proxy_url
    }
    
    url = f"https://www.ofiii.com/channel/watch/{slug}"

    try:
        # 解锁器(Unblocker)会自动渲染网页，不需要安装浏览器
        # 我们直接请求网页源码
        response = requests.get(url, proxies=proxies, timeout=60, verify=False)
        
        if response.status_code == 200:
            # 在返回的文字里寻找 AssetID
            match = re.search(r'playlist/([a-z0-9A-Z_-]+)/', response.text)
            if match:
                aid = match.group(1)
                print(f"✅ 成功获取: {cid} -> {aid}")
                return aid
            else:
                print(f"⚠️ 网页已打开，但没发现播放地址。")
        else:
            print(f"❌ 访问失败，错误码: {response.status_code}")
            if response.status_code == 407:
                print("💡 提示：还是认证失败，请检查 Bright Data 后台是否放开了 IP 白名单(Any)")
                
    except Exception as e:
        print(f"🔥 发生错误: {e}")
    return None

def main():
    channels = {
        'lhtv01': 'litv-longturn03', 'lhtv02': 'litv-longturn21',
        'lhtv03': 'litv-longturn18', 'lhtv04': 'litv-longturn11',
        'lhtv05': 'litv-longturn12', 'lhtv06': 'litv-longturn01',
        'lhtv07': 'litv-longturn02'
    }
    
    worker_file = "workers.js"
    if not os.path.exists(worker_file):
        print("❌ 找不到 workers.js")
        return

    with open(worker_file, "r", encoding="utf-8") as f:
        content = f.read()

    updated = False
    for cid, slug in channels.items():
        aid = get_asset_id(cid, slug)
        if aid:
            # 自动寻找并替换 key: "..." 部分
            pattern = rf'"{cid}"\s*:\s*\{{[^}}]*?key\s*:\s*["\'][^"\']*["\']'
            replacement = f'"{cid}": {{ name: "", key: "{aid}" }}'
            content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            updated = True
        time.sleep(2)

    if updated:
        with open(worker_file, "w", encoding="utf-8") as f:
            f.write(content)
        print("🎉 所有频道已同步完毕！")

if __name__ == "__main__":
    main()
