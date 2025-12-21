import os, re, time, requests
import urllib3

# 禁用红色的证书警告，让日志更整洁
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_asset_id(cid, slug):
    print(f"🔍 正在处理频道: {cid}...")
    
    # --- 填入你截图中的准确信息 ---
    # 住宅代理用户名后加 -country-tw 强制使用台湾 IP
    user = "brd-customer-hl_739668d7-zone-residential_proxy1-country-tw"
    password = "me6lrg0ysg96"
    
    # 构造代理 URL
    proxy_url = f"http://{user}:{password}@brd.superproxy.io:33335"
    
    proxies = {
        "http": proxy_url,
        "https": proxy_url
    }
    
    target_url = f"https://www.ofiii.com/channel/watch/{slug}"

    try:
        # 使用住宅代理发起请求
        # 住宅代理模仿真实用户，Ofiii 极难拦截
        response = requests.get(target_url, proxies=proxies, timeout=60, verify=False)
        
        if response.status_code == 200:
            content = response.text
            # 搜索网页代码里的 AssetID
            match = re.search(r'playlist/([a-z0-9A-Z_-]+)/', content)
            if match:
                aid = match.group(1)
                print(f"✅ 提取成功: {aid}")
                return aid
            else:
                print(f"⚠️ 网页已连接，但没搜到 ID。可能需要后台开启『Web Unlocker』功能。")
        else:
            print(f"❌ 访问失败，错误码: {response.status_code}")
            if response.status_code == 407:
                print("💡 提示：407 代表密码错了，或者没在后台把白名单设为 Any")
            
    except Exception as e:
        print(f"🔥 发生异常: {e}")
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
        print("❌ 错误: 找不到 workers.js")
        return

    with open(worker_file, "r", encoding="utf-8") as f:
        content = f.read()

    updated = False
    for cid, slug in channels.items():
        aid = get_asset_id(cid, slug)
        if aid:
            # 替换 workers.js 中的 key 值
            pattern = rf'"{cid}"\s*:\s*\{{[^}}]*?key\s*:\s*["\'][^"\']*["\']'
            replacement = f'"{cid}": {{ name: "", key: "{aid}" }}'
            content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            updated = True
        time.sleep(3) # 住宅代理稍微等一下更安全

    if updated:
        with open(worker_file, "w", encoding="utf-8") as f:
            f.write(content)
        print("🚀 同步完成，workers.js 已更新！")

if __name__ == "__main__":
    main()
