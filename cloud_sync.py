import os, re, time, requests, json, urllib3
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class OfiiiDebugger:
    def __init__(self):
        # --- 建议检查点：API_TOKEN 是否包含前后空格？Zone 名字是否带下划线？ ---
        self.api_token = "76b7e42b-9c49-4acb-819a-3f90b45be668"
        self.zone_name = "unblocker_ofiii"
        self.api_url = "https://api.brightdata.com/request"
        self.worker_file = "workers.js"
        
        self.channels = {
            'lhtv01': 'litv-longturn03', 'lhtv02': 'litv-longturn21',
            'lhtv03': 'litv-longturn18', 'lhtv04': 'litv-longturn11',
            'lhtv05': 'litv-longturn12', 'lhtv06': 'litv-longturn01',
            'lhtv07': 'litv-longturn02'
        }

    def log(self, step, message, status="INFO"):
        curr_time = datetime.now().strftime('%H:%M:%S')
        print(f"[{curr_time}] [{status}] Stage: {step} >> {message}")

    def debug_asset_id(self, cid, slug):
        self.log("INIT", f"开始处理频道 {cid} (URL: {slug})")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_token}"
        }
        
        payload = {
            "zone": self.zone_name,
            "url": f"https://www.ofiii.com/channel/watch/{slug}",
            "format": "raw",
            "country": "tw",
            "render": True,
            "actions": [
                {"wait": ".video-player"},
                {"click": ".vjs-big-play-button"},
                {"wait": 10000}
            ]
        }

        try:
            self.log("AUTH", f"正在发送请求到 Bright Data API... (Zone: {self.zone_name})")
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=120)
            
            # --- 环节 1: 权限验证 ---
            if response.status_code == 401:
                self.log("AUTH", "❌ 认证失败 (401)！原因：API Token 无效或已过期。", "ERROR")
                print(f"   [调试信息] 请核对后台 Token 列表，当前使用的是: {self.api_token[:8]}****")
                return None
            
            if response.status_code == 403:
                self.log("AUTH", "❌ 权限拒绝 (403)！原因：可能 Zone 名字写错，或者账户余额不足。", "ERROR")
                return None

            # --- 环节 2: 渲染状态 ---
            self.log("RENDER", f"API 握手成功 (HTTP {response.status_code})，正在解析返回内容...")
            
            content = response.text
            if not content:
                self.log("DATA", "❌ 网页返回为空，浏览器可能未能成功加载页面。", "ERROR")
                return None

            # --- 环节 3: 模拟点击与 ID 提取 ---
            self.log("SCRAPE", "正在搜索 HTML 源码中的 AssetID 模式...")
            match = re.search(r'playlist/([a-z0-9A-Z_-]+)/', content)
            
            if match:
                aid = match.group(1)
                self.log("SCRAPE", f"✨ 提取成功！ID: {aid}", "SUCCESS")
                return aid
            else:
                self.log("SCRAPE", "⚠️ 未能找到 ID。可能是点击动作未触发，或网页结构变动。", "WARNING")
                # 打印一小段源码辅助判断
                print(f"   [源码预览]: {content[:200].replace('', '')}...")
                
        except Exception as e:
            self.log("SYSTEM", f"🔥 发生网络崩溃或代码错误: {str(e)}", "CRITICAL")
        
        return None

    def start(self):
        self.log("START", "==== 自动化任务调试启动 ====")
        if not os.path.exists(self.worker_file):
            self.log("FILE", f"找不到 {self.worker_file}", "ERROR")
            return

        with open(self.worker_file, "r", encoding="utf-8") as f:
            content = f.read()

        updated_count = 0
        for cid, slug in self.channels.items():
            new_id = self.debug_asset_id(cid, slug)
            if new_id:
                pattern = rf'"{cid}"\s*:\s*\{{[^}}]*?key\s*:\s*["\'][^"\']*["\']'
                replacement = f'"{cid}": {{ name: "", key: "{new_id}" }}'
                content = re.sub(pattern, replacement, content, flags=re.DOTALL)
                updated_count += 1
            
            print("-" * 50)
            time.sleep(5)

        if updated_count > 0:
            with open(self.worker_file, "w", encoding="utf-8") as f:
                f.write(content)
            self.log("END", f"任务结束。更新了 {updated_count} 个频道。", "SUCCESS")
        else:
            self.log("END", "任务结束。没有数据被更新。", "INFO")

if __name__ == "__main__":
    debugger = OfiiiDebugger()
    debugger.start()
