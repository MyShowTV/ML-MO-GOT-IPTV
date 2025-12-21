import os
import re
import time
import requests
import json
import urllib3

# 1. 禁用 SSL 证书警告，保持日志清爽
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_asset_id(cid, slug):
    """
    通过台湾住宅代理，模拟浏览器点击播放，抓取动态生成的 AssetID
    """
    print(f"🔍 正在处理频道: {cid} ({slug})...")
    
    # --- 住宅代理认证信息 (由你提供) ---
    proxy_user = "brd-customer-hl_739668d7-zone-residential_proxy1-country-tw"
    proxy_pass = "me6lrg0ysg96"
    proxy_host = "brd.superproxy.io:33335"
    
    proxy_url = f"http://{proxy_user}:{proxy_pass}@{proxy_host}"
    proxies = {
        "http": proxy_url,
        "https": proxy_url
    }
    
    # --- 核心：通过 Header 注入自动化指令 ---
    # 告诉 Bright Data：开启渲染 -> 点击播放 -> 等待 ID 生成
    headers = {
        "x-api-render": "true",
        "x-api-actions": json.dumps([
            {"wait": ".vjs-big-play-button"},      # 等待播放按钮出现
            {"click": ".vjs-big-play-button"},     # 模拟真实点击
            {"wait": 6000}                         # 点击后强制等待 6 秒让链接生成
        ])
    }

    target_url = f"https://www.ofiii.com/channel/watch/{slug}"

    try:
        # 发起请求
        response = requests.get(
            target_url, 
            proxies=proxies, 
            headers=headers, 
            timeout=120, 
            verify=False
        )
        
        if response.status_code == 200:
            content = response.text
            # 从返回的已渲染 HTML 中匹配 playlist/ID/
            match = re.search(r'playlist/([a-z0-9A-Z_-]+)/', content)
            
            if match:
                aid = match.group(1)
                print(f"✅ 成功抓取 ID: {aid}")
                return aid
            else:
                print(f"⚠️ 网页已连接，但模拟点击后未发现 ID。请检查后台是否开启了 Web Unlocker 权限。")
        else:
            print(f"❌ 访问失败，错误码: {response.status_code}")
            if response.status_code == 407:
                print("💡 提示：请确保 Bright Data 后台的 IP 白名单已设为 Any。")
                
    except Exception as e:
        print(f"🔥 网络异常: {e}")
    return None

def main():
    # 需要更新的频道列表：频道名 -> 网址后缀
    channels = {
        'lhtv01': 'litv-longturn03', 'lhtv02': 'litv-longturn21',
        'lhtv03': 'litv-longturn18', 'lhtv04': 'litv-longturn11',
        'lhtv05': 'litv-longturn12', 'lhtv06': 'litv-longturn01',
        'lhtv07': 'litv-longturn02'
    }
    
    # 2. 定位 workers.js 文件
    worker_file = "workers.js"
    if not os.path.exists(worker_file):
        print(f"❌ 错误: 在当前目录下没找到 {worker_file}")
        return

    # 读取旧文件
    with open(worker_file, "r", encoding="utf-8") as f:
        worker_content = f.read()

    is_any_updated = False
    
    # 3. 逐个频道抓取并替换
    for cid, slug in channels.items():
        new_key = get_asset_id(cid, slug)
        
        if new_key:
            # 使用正则匹配替换：找到 "lhtv01": { ... key: "旧KEY" }
            # 这里的正则兼容双引号和单引号
            pattern = rf'"{cid}"\s*:\s*\{{[^}}]*?key\s*:\s*["\'][^"\']*["\']'
            replacement = f'"{cid}": {{ name: "", key: "{new_key}" }}'
            
            worker_content = re.sub(pattern, replacement, worker_content, flags=re.DOTALL)
            is_any_updated = True
        
        # 住宅代理较慢，且为了防止被封，每个请求间隔 5 秒
        time.sleep(5)

    # 4. 如果有更新，写回文件
    if is_any_updated:
        with open(worker_file, "w", encoding="utf-8") as f:
            f.write(worker_content)
        print("🚀 同步成功！workers.js 已更新。")
    else:
        print("💡 本次未更新任何内容。")

if __name__ == "__main__":
    main()
