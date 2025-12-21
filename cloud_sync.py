import os, re, time, requests, json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_asset_id(cid, slug):
    print(f"🔍 正在深度探测频道: {cid}...")
    
    api_url = "https://api.brightdata.com/request"
    api_token = "76b7e42b-9c49-4acb-819a-3f90b45be668"
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    # 构建更真实的模拟环境
    data = {
        "zone": "unblocker_ofiii",
        "url": f"https://www.ofiii.com/channel/watch/{slug}",
        "format": "raw",
        "country": "tw",
        "proxy_type": "residential", # 坚持走住宅 IP
        "render": True,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "actions": [
            # 1. 等待视频容器加载
            {"wait": ".video-player"}, 
            # 2. 尝试点击多个可能的播放按钮标识符 (增加容错)
            {"click": ".vjs-big-play-button"}, 
            {"click": "button[aria-label='Play']"},
            # 3. 强制等待，让 JS 把 m3u8 地址写进 HTML
            {"wait": 8000}
        ]
    }

    try:
        response = requests.post(api_url, headers=headers, json=data, timeout=150)
        
        if response.status_code == 200:
            content = response.text
            
            # 匹配模式1: 常见的 playlist 链接
            match = re.search(r'playlist/([a-z0-9A-Z_-]+)/', content)
            if not match:
                # 匹配模式2: 源码中的 assetId 变量
                match = re.search(r'assetId["\']\s*:\s*["\']([^"\']+)["\']', content)
            
            if match:
                aid = match.group(1)
                print(f"✨ 抓取成功: {cid} -> {aid}")
                return aid
            else:
                # 打印一小段源码进行调试，看看是否被跳到了 403 页面
                print(f"⚠️ 无法匹配 ID。返回内容片段: {content[:150].strip()}")
        else:
            print(f"❌ API 状态异常: {response.status_code}")
            
    except Exception as e:
        print(f"🔥 运行异常: {e}")
    return None

def main():
    channels = {
        'lhtv01': 'litv-longturn03', 'lhtv02': 'litv-longturn21',
        'lhtv03': 'litv-longturn18', 'lhtv04': 'litv-longturn11',
        'lhtv05': 'litv-longturn12', 'lhtv06': 'litv-longturn01',
        'lhtv07': 'litv-longturn02'
    }
    
    worker_file = "workers.js"
    if not os.path.exists(worker_file): return
    with open(worker_file, "r", encoding="utf-8") as f:
        content = f.read()

    is_any_updated = False
    for cid, slug in channels.items():
        aid = get_asset_id(cid, slug)
        if aid:
            # 更新 workers.js 里的 key
            pattern = rf'"{cid}"\s*:\s*\{{[^}}]*?key\s*:\s*["\'][^"\']*["\']'
            replacement = f'"{cid}": {{ name: "", key: "{aid}" }}'
            content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            is_any_updated = True
        time.sleep(12) # 住宅+渲染非常耗资源，频道间距拉长

    if is_any_updated:
        with open(worker_file, "w", encoding="utf-8") as f:
            f.write(content)
        print("🚀 workers.js 更新已推送到文件！")

if __name__ == "__main__":
    main()
