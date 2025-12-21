import os, re, time, requests, json, urllib3
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class OfiiiApiInterceptor:
    def __init__(self):
        # 住宅代理凭据
        self.proxy_host = "brd.superproxy.io:33335"
        self.proxy_user = "brd-customer-hl_739668d7-zone-residential_proxy1-country-tw"
        self.proxy_pass = "me6lrg0ysg96"
        
        self.worker_file = "workers.js"
        self.channels = {
            'lhtv01': 'litv-longturn03', 'lhtv02': 'litv-longturn21',
            'lhtv03': 'litv-longturn18', 'lhtv04': 'litv-longturn11',
            'lhtv05': 'litv-longturn12', 'lhtv06': 'litv-longturn01',
            'lhtv07': 'litv-longturn02'
        }

    def intercept_m3u8(self, cid, slug):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🕵️ 拦截模式启动: {cid}")
        
        proxy_url = f"http://{self.proxy_user}:{self.proxy_pass}@{self.proxy_host}"
        proxies = {"http": proxy_url, "https": proxy_url}
        
        # --- 核心修改：让 Bright Data 像浏览器控制台一样监控网络 ---
        headers = {
            "x-api-render": "true",
            "x-api-actions": json.dumps([
                {"wait": ".video-player"},
                {"click": ".vjs-big-play-button"},
                {"wait": 15000} # 等待加载正片
            ])
        }

        try:
            # 1. 首先尝试请求主页并拦截
            url = f"https://www.ofiii.com/channel/watch/{slug}"
            response = requests.get(url, proxies=proxies, headers=headers, timeout=180, verify=False)
            
            # 2. 在整个响应（包含 JS 执行后的 DOM）中深度搜索带有 avc1 的 m3u8 
            # 刚才你提供的 ID 包含 "avc1"，我们直接以此为特征码
            content = response.text
            
            # 匹配包含 avc1 和 m3u8 的最长字符串
            pattern = r'([^\s"\'<>]+avc1[^\s"\'<>]+?\.m3u8)'
            match = re.search(pattern, content)
            
            if not match:
                # 备选方案：找任何带有 litv 前缀的 m3u8
                pattern = r'([^\s"\'<>]+litv[^\s"\'<>]+?\.m3u8)'
                match = re.search(pattern, content)

            if match:
                m3u8_full = match.group(1)
                # 提取文件名部分作为 Key
                key = m3u8_full.split('/')[-1]
                print(f"✅ 拦截成功！Key: {key}")
                return key
            else:
                print(f"❌ 页面已渲染，但流量中未发现符合 'avc1' 格式的 m3u8 链接。")
                # 打印一小段 video 相关的源码进行最后确认
                v_idx = content.find('video')
                if v_idx != -1:
                    print(f"   [Video 上下文]: {content[v_idx:v_idx+300]}")

        except Exception as e:
            print(f"🔥 异常: {e}")
        return None

    def run(self):
        if not os.path.exists(self.worker_file): return
        with open(self.worker_file, "r", encoding="utf-8") as f:
            content = f.read()

        updated = False
        for cid, slug in self.channels.items():
            new_key = self.intercept_m3u8(cid, slug)
            if new_key:
                # 针对你提供的格式 (包含 = 和 空格) 的正则更新
                pattern = rf'"{cid}"\s*:\s*\{{[^}}]*?key\s*:\s*["\'][^"\']*["\']'
                replacement = f'"{cid}": {{ name: "", key: "{new_key}" }}'
                content = re.sub(pattern, replacement, content, flags=re.DOTALL)
                updated = True
            time.sleep(10)

        if updated:
            with open(self.worker_file, "w", encoding="utf-8") as f:
                f.write(content)
            print("🚀 数据已同步到 workers.js")
        else:
            print("💡 未发现更新。")

if __name__ == "__main__":
    OfiiiApiInterceptor().run()
