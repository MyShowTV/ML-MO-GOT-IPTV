import os, re, time, requests, json
import urllib3

# 禁用证书警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_asset_id(cid, slug):
    print(f"🌐 正在通过 API 启动云端真机浏览器: {cid}...")
    
    # --- 你的 API 核心配置 ---
    api_url = "https://api.brightdata.com/request"
    api_token = "76b7e42b-9c49-4acb-819a-3f90b45be668"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_token}"
    }
    
    # --- 深度模拟指令 (JSON 格式) ---
    data = {
        "zone": "unblocker_ofiii",
        "url": f"https://www.ofiii.com/channel/watch/{slug}",
        "format": "raw",
        "country": "tw",           # 锁定台湾 IP
        "render": True,            # 开启云端真机渲染
        # 伪装成真实的 Windows 10 PC 浏览器
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "actions": [
            {"wait": ".video-player"},           # 等待播放器框架
            {"scroll_to": ".video-player"},      # 滚动到视野内（模拟真人看视频）
            {"click": ".vjs-big-play-button"},   # 【关键】真实点击播放按钮
            {"wait": 10000}                      # 强制停留 10 秒，拦截生成的 m3u8 ID
        ]
    }

    try:
        # 向 Bright Data 的 API 发送 POST 请求
        response = requests.post(api_url, headers=headers, json=data, timeout=180)
        
        if response.status_code == 200:
            content = response.text
            
            # 从返回的完整渲染代码中抓取 AssetID
            # 匹配模式：playlist/后面那一串动态 ID
            match = re.search(r'playlist/([a-z0-9A-Z_-]+)/', content)
            
            if match:
                aid = match.group(1)
                print(f"✨ 真机模拟成功！ID: {aid}")
                return aid
            else:
                # 打印标题，确认是否成功进入了台湾网页
                title = re.search(r'<title>(.*?)</title>', content)
                print(f"⚠️ 点击已执行，但未提取到 ID。网页标题: {title.group(1) if title else '未知'}")
        else:
            print(f"❌ API 响应错误: {response.status_code} - {response.text[:200]}")
            
    except Exception as e:
        print(f"🔥 运行异常: {e}")
    return None

def main():
    # 频道配置
    channels = {
        'lhtv01': 'litv-longturn03', 'lhtv02': 'litv-longturn21',
        'lhtv03': 'litv-longturn18', 'lhtv04': 'litv-longturn11',
        'lhtv05': 'litv-longturn12', 'lhtv06': 'litv-longturn01',
        'lhtv07': 'litv-longturn02'
    }
    
    worker_file = "workers.js"
    if not os.path.exists(worker_file):
        print(f"❌ 错误: 找不到 {worker_file}")
        return

    with open(worker_file, "r", encoding="utf-8") as f:
        content = f.read()

    updated = False
    for cid, slug in channels.items():
        aid = get_asset_id(cid, slug)
        if aid:
            # 更新 workers.js
            pattern = rf'"{cid}"\s*:\s*\{{[^}}]*?key\s*:\s*["\'][^"\']*["\']'
            replacement = f'"{cid}": {{ name: "", key: "{aid}" }}'
            content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            updated = True
        
        # 这种高强度模拟非常吃资源，请在频道间保持长间隔
        time.sleep(15)

    if updated:
        with open(worker_file, "w", encoding="utf-8") as f:
            f.write(content)
        print("🚀 workers.js 更新完毕！")
    else:
        print("💡 本次未发现变动，未更新文件。")

if __name__ == "__main__":
    main()
