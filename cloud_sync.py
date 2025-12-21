import os, re, time, requests, json, urllib3
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class OfiiiDeepScan:
    def __init__(self):
        # 你的住宅代理配置 (保持不变，因为这是通的)
        self.proxy_host = "brd.superproxy.io:33335"
        self.proxy_user = "brd-customer-hl_739668d7-zone-residential_proxy1-country-tw"
        self.proxy_pass = "me6lrg0ysg96"
        
        self.worker_file = "workers.js"
        # 既然都通了，我们只测试一个频道，节省时间，专注分析源码
        self.target_channel = {'cid': 'lhtv01', 'slug': 'litv-longturn03'}

    def scan_page(self):
        cid = self.target_channel['cid']
        slug = self.target_channel['slug']
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔬 深度解剖频道: {cid} ({slug})")
        
        proxy_url = f"http://{self.proxy_user}:{self.proxy_pass}@{self.proxy_host}"
        proxies = {"http": proxy_url, "https": proxy_url}
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "x-api-render": "true",
            "x-api-actions": json.dumps([
                {"wait": ".video-player"},
                {"click": ".vjs-big-play-button"},
                {"wait": 15000} # 保持长等待，确保 m3u8 加载进 DOM
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
            print(f"📄 页面下载完成，长度: {len(content)}")

            # --- 🕵️‍♂️ 侦探模式：抓取所有可疑链接 ---
            
            print("\n--- 🔎 搜索结果 (m3u8) ---")
            # 1. 抓取所有 .m3u8 结尾的链接 (宽泛匹配)
            # 匹配 http 或 / 开头，直到遇到引号或空格
            m3u8_matches = re.findall(r'["\'](https?://[^"\'\s]+\.m3u8[^"\'\s]*)["\']', content)
            if m3u8_matches:
                for url in m3u8_matches:
                    print(f"🎯 发现潜在 m3u8: {url}")
            else:
                print("❌ 未发现标准 .m3u8 链接")

            print("\n--- 🔎 搜索结果 (包含 litv 关键词) ---")
            # 2. 抓取所有包含 litv 的 URL (可能是 mp4 或 json)
            litv_matches = re.findall(r'["\'](https?://[^"\'\s]*litv[^"\'\s]*)["\']', content)
            if litv_matches:
                for url in litv_matches:
                    print(f"🔗 发现 litv 相关链接: {url}")
            else:
                print("❌ 未发现 litv 相关链接")

            # 3. 如果上面都没找到，打印一小段包含 'player' 的上下文
            if not m3u8_matches and not litv_matches:
                print("\n--- ⚠️ 源码上下文快照 ---")
                # 找 video 标签附近的内容
                idx = content.find('video')
                if idx != -1:
                    print(content[idx:idx+500])
                else:
                    print("未找到 video 标签")

        except Exception as e:
            print(f"🔥 异常: {e}")

if __name__ == "__main__":
    OfiiiDeepScan().scan_page()
