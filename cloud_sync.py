import os, re, time, requests, json, urllib3
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class OfiiiFinalSolution:
    def __init__(self):
        # --- 使用你截图里确认成功的住宅代理凭据 ---
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

    def get_asset_id(self, cid, slug):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 启动住宅代理模拟: {cid}")
        
        proxy_url = f"http://{self.proxy_user}:{self.proxy_pass}@{self.proxy_host}"
        proxies = {"http": proxy_url, "https": proxy_url}
        
        # 使用 Header 注入指令，绕过 API Token 验证
        headers = {
            "x-api-render": "true", # 启用云端浏览器渲染
            "x-api-actions": json.dumps([
                {"wait": ".vjs-big-play-button"},
                {"click": ".vjs-big-play-button"},
                {"wait": 12000} # 给足时间加载 m3u8
            ])
        }

        try:
            # 这里的 URL 是目标网页，认证信息在代理链接里
            response = requests.get(
                f"https://www.ofiii.com/channel/watch/{slug}",
                proxies=proxies,
                headers=headers,
                timeout=180,
                verify=False
            )
            
            if response.status_code == 200:
                # 提取 AssetID
                match = re.search(r'playlist/([a-z0-9A-Z_-]+)/', response.text)
                if match:
                    aid = match.group(1)
                    print(f"✨ 提取成功: {aid}")
                    return aid
                else:
                    print(f"⚠️ 网页已打开但未找到 ID。长度: {len(response.text)}")
            else:
                print(f"❌ 错误码: {response.status_code}。请确认后台白名单是否设为 Any。")
        except Exception as e:
            print(f"🔥 请求异常: {e}")
        return None

    def run(self):
        if not os.path.exists(self.worker_file): return
        with open(self.worker_file, "r", encoding="utf-8") as f:
            content = f.read()

        updated = False
        for cid, slug in self.channels.items():
            aid = self.get_asset_id(cid, slug)
            if aid:
                pattern = rf'"{cid}"\s*:\s*\{{[^}}]*?key\s*:\s*["\'][^"\']*["\']'
                replacement = f'"{cid}": {{ name: "", key: "{aid}" }}'
                content = re.sub(pattern, replacement, content, flags=re.DOTALL)
                updated = True
            time.sleep(10)

        if updated:
            with open(self.worker_file, "w", encoding="utf-8") as f:
                f.write(content)
            print("🚀 [DONE] workers.js 更新成功！")

if __name__ == "__main__":
    OfiiiFinalSolution().run()
