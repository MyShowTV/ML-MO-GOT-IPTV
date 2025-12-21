import os, re, time, requests

def get_asset_id(cid, slug):
    print(f"🔍 正在同步: {cid}...")
    
    # 这里的名字必须和你 Bright Data 后台的 Zone 名字一模一样
    zone_user = "brd-customer-hl_739668d7-zone-unblocker_ofiii-country-tw"
    # 从保险柜读取你的密码
    password = os.getenv("MY_BRD_PASS") 
    
    proxy_url = f"http://{zone_user}:{password}@brd.superproxy.io:22225"
    proxies = {"http": proxy_url, "https": proxy_url}
    
    target_url = f"https://www.ofiii.com/channel/watch/{slug}"

    try:
        # 解锁器会自动处理台湾 IP 和网页渲染，不需要 Selenium
        response = requests.get(target_url, proxies=proxies, timeout=60, verify=False)
        
        if response.status_code == 200:
            # 在网页代码里找 AssetID
            match = re.search(r'playlist/([a-z0-9A-Z_-]+)/', response.text)
            if match:
                aid = match.group(1)
                print(f"✅ 成功抓到: {aid}")
                return aid
        print(f"❌ 失败，状态码: {response.status_code} (请检查余额或Zone名)")
    except Exception as e:
        print(f"🔥 出错了: {e}")
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
        print("❌ 找不到 workers.js 文件")
        return

    with open(worker_file, "r", encoding="utf-8") as f:
        content = f.read()

    is_changed = False
    for cid, slug in channels.items():
        aid = get_asset_id(cid, slug)
        if aid:
            # 这里的正则会自动把旧的 key 替换成新的
            pattern = rf'"{cid}"\s*:\s*\{{[^}}]*?key\s*:\s*["\'][^"\']*["\']'
            replacement = f'"{cid}": {{ name: "", key: "{aid}" }}'
            content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            is_changed = True
        time.sleep(2)

    if is_changed:
        with open(worker_file, "w", encoding="utf-8") as f:
            f.write(content)
        print("🎉 全部更新成功！")

if __name__ == "__main__":
    main()
