import os, re, time, requests, json, urllib3
from datetime import datetime

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class OfiiiOmniParser:
    def __init__(self):
        # 1. 你的住宅代理凭据 (已验证通过)
        self.proxy_host = "brd.superproxy.io:33335"
        self.proxy_user = "brd-customer-hl_739668d7-zone-residential_proxy1-country-tw"
        self.proxy_pass = "me6lrg0ysg96"
        
        self.worker_file = "workers.js"
        # 频道映射
        self.channels = {
            'lhtv01': 'litv-longturn03', 'lhtv02': 'litv-longturn21',
            'lhtv03': 'litv-longturn18', 'lhtv04': 'litv-longturn11',
            'lhtv05': 'litv-longturn12', 'lhtv06': 'litv-longturn01',
            'lhtv07': 'litv-longturn02'
        }

    def get_asset_id(self, cid, slug):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔍 正在探测频道: {cid} ({slug})")
        
        # 构造代理 URL
        proxy_url = f"http://{self.proxy_user}:{self.proxy_pass}@{self.proxy_host}"
        proxies = {"http": proxy_url, "https": proxy_url}
        
        # 2. 增强型 Header 指令
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.google.com/",  # 伪装来源
            # 告诉 Bright Data 开启浏览器并执行点击
            "x-api-render": "true",
            "x-api-actions": json.dumps([
                {"wait": ".video-player"},          # 等待播放器
                {"click": ".vjs-big-play-button"},  # 点击播放
                {"wait": 15000}                     # 【加长】等待15秒，确保广告跑完显示正片
            ])
        }

        try:
            response = requests.get(
                f"https://www.ofiii.com/channel/watch/{slug}",
                proxies=proxies,
                headers=headers,
                timeout=180,
                verify=False
            )
            
            content = response.text
            
            # --- 3. 页面诊断 (关键调试信息) ---
            page_title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
            page_title = page_title_match.group(1) if page_title_match else "未知标题"
            
            if response.status_code == 200:
                # --- 4. 三重正则匹配策略 ---
                
                # 策略 A: 匹配 playlist 链接 (最常见)
                match = re.search(r'playlist/([a-z0-9A-Z_-]+)/', content)
                
                # 策略 B: 匹配 JSON 变量 assetId
                if not match:
                    match = re.search(r'assetId["\']\s*:\s*["\']([^"\']+)["\']', content)
                    
                # 策略 C: 匹配 vod_id
                if not match:
                    match = re.search(r'vod_id["\']\s*:\s*["\']([^"\']+)["\']', content)
                
                if match:
                    aid = match.group(1)
                    print(f"✅ 成功提取 ID: {aid}")
                    return aid
                else:
                    # 打印失败原因分析
                    print(f"⚠️ 未找到 ID。")
                    print(f"   - 网页标题: 【{page_title}】")
                    print(f"   - 源码长度: {len(content)}")
                    if "Just a moment" in page_title or "Attention Required" in page_title:
                        print("   ❌ 结果: 被 Cloudflare 拦截了，正在尝试重新握手...")
                    elif "404" in page_title:
                        print("   ❌ 结果: 视频页面不存在。")
            else:
                print(f"❌ 请求失败: {response.status_code}")
                
        except Exception as e:
            print(f"🔥 网络异常: {e}")
        return None

    def run(self):
        if not os.path.exists(self.worker_file): return
        with open(self.worker_file, "r", encoding="utf-8") as f:
            content = f.read()

        updated_count = 0
        for cid, slug in self.channels.items():
            aid = self.get_asset_id(cid, slug)
            if aid:
                # 更新逻辑
                pattern = rf'"{cid}"\s*:\s*\{{[^}}]*?key\s*:\s*["\'][^"\']*["\']'
                replacement = f'"{cid}": {{ name: "", key: "{aid}" }}'
                content = re.sub(pattern, replacement, content, flags=re.DOTALL)
                updated_count += 1
            
            # 稍微休息一下，避免并发过高
            time.sleep(8)

        if updated_count > 0:
            with open(self.worker_file, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"🚀 更新完成！共更新 {updated_count} 个频道。")
        else:
            print("💡 扫描结束，未发现新 ID。")

if __name__ == "__main__":
    OfiiiOmniParser().run()
