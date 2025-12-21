import os, re, time, requests, json, urllib3
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class OfiiiFinalHunter:
    def __init__(self):
        # 住宅代理凭据
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

    def capture_secret_key(self, cid, slug):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🛡️ 正在攻克频道: {cid} ({slug})")
        
        proxy_url = f"http://{self.proxy_user}:{self.proxy_pass}@{self.proxy_host}"
        proxies = {"http": proxy_url, "https": proxy_url}
        
        # 指令：开启浏览器渲染 + 执行点击 + 捕获网络日志
        headers = {
            "x-api-render": "true",
            "x-api-actions": json.dumps([
                {"wait": ".video-player"},
                {"click": ".vjs-big-play-button"},
                {"wait": 15000}  # 给足 15 秒让浏览器发出 m3u8 请求
            ])
        }

        try:
            url = f"https://www.ofiii.com/channel/watch/{slug}"
            response = requests.get(url, proxies=proxies, headers=headers, timeout=180, verify=False)
            
            # 在返回的所有内容（包括网络日志快照）中搜索 /playlist/ 结构
            content = response.text
            
            # 正则 A：提取完整结构 /playlist/密匙/文件名.m3u8
            # 兼容你提供的格式： NIySmp86SwI/litv-longturn03-avc1_336000=1-mp4a_114000=2.m3u8
            pattern = r'playlist/([a-zA-Z0-9_-]+)/([^"\'\s]+\.m3u8)'
            match = re.search(pattern, content)
            
            if match:
                secret_id = match.group(1)   # NIySmp86SwI
                file_name = match.group(2)   # litv-longturn03...m3u8
                
                # 组合成完整的 Key 存入 workers.js
                # 按照你的需求，存储为 /playlist/密匙/文件名 这种格式
                final_key = f"{secret_id}/{file_name}"
                print(f"✨ 成功截获！\n   ID: {secret_id}\n   File: {file_name}")
                return final_key
            else:
                print(f"❌ 捕获失败。页面已渲染，但未在网络请求中发现 /playlist/ 路径。")
                # 辅助诊断：看看有没有 playlist 关键字
                if "playlist" in content:
                    print("   [提示] 源码中包含 'playlist' 单词，但格式不符，请检查正则表达式。")

        except Exception as e:
            print(f"🔥 异常: {e}")
        return None

    def run(self):
        if not os.path.exists(self.worker_file): return
        with open(self.worker_file, "r", encoding="utf-8") as f:
            js_content = f.read()

        any_updated = False
        for cid, slug in self.channels.items():
            result = self.capture_secret_key(cid, slug)
            if result:
                # 针对 workers.js 的 Key 进行精准替换
                # 匹配 "lhtv01": { ... key: "旧值" }
                pattern = rf'"{cid}"\s*:\s*\{{[^}}]*?key\s*:\s*["\'][^"\']*["\']'
                replacement = f'"{cid}": {{ name: "", key: "{result}" }}'
                js_content = re.sub(pattern, replacement, js_content, flags=re.DOTALL)
                any_updated = True
            
            time.sleep(10) # 频道切换间隔

        if any_updated:
            with open(self.worker_file, "w", encoding="utf-8") as f:
                f.write(js_content)
            print("🚀 [SUCCESS] 所有频道 Key 已同步到 workers.js")
        else:
            print("💡 未发现任何有效更新。")

if __name__ == "__main__":
    hunter = OfiiiFinalHunter()
    hunter.run()
