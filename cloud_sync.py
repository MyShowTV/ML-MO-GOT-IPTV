import os, re, time, requests, json, urllib3
from datetime import datetime

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class OfiiiM3u8Hunter:
    def __init__(self):
        # 你的住宅代理凭据 (已验证通过)
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

    def get_m3u8_file(self, cid, slug):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🎯 正在锁定 .m3u8 文件: {cid}")
        
        proxy_url = f"http://{self.proxy_user}:{self.proxy_pass}@{self.proxy_host}"
        proxies = {"http": proxy_url, "https": proxy_url}
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "x-api-render": "true",
            "x-api-actions": json.dumps([
                {"wait": ".video-player"},
                {"click": ".vjs-big-play-button"},
                # 点击后等待 12 秒，确保那个复杂的 m3u8 链接加载出来
                {"wait": 12000}
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
            
            # --- 核心修改：针对你提供的复杂文件名进行匹配 ---
            # 规则：抓取所有以 .m3u8 结尾，且包含字母、数字、横杠、下划线、等号的字符串
            # 这里的 [^"\'<>\s] 表示“除了引号、尖括号和空格之外的所有字符”
            match = re.search(r'([^"\'<>\s/]+\.m3u8)', content)
            
            if match:
                # 抓取到的完整文件名，例如：litv-longturn03-avc1_736000=3-mp4a_114000=2.m3u8
                full_m3u8 = match.group(1)
                
                # 如果你需要提取 ID (比如 litv-longturn03-avc1...)，我们可以在这里截取
                # 但根据你的需求，这里先直接抓取整个文件名，或者提取中间那段核心 ID
                # 假设你要提取的是 'playlist/' 和 '.m3u8' 之间的部分：
                
                print(f"✅ 抓取成功: {full_m3u8}")
                
                # 为了适配 workers.js，我们可能需要把文件名处理一下，
                # 如果 workers.js 只需要 key，我们这里先返回整个文件名试试
                return full_m3u8
            else:
                print(f"⚠️ 页面已加载 (长度:{len(content)})，但未匹配到 .m3u8 文件。")
                # 调试：打印一下有没有包含 'avc1' 这个关键词
                if 'avc1' in content:
                    print("   提示：源码中发现了 'avc1'，说明文件存在，是正则没对上！")

        except Exception as e:
            print(f"🔥 异常: {e}")
        return None

    def run(self):
        if not os.path.exists(self.worker_file): return
        with open(self.worker_file, "r", encoding="utf-8") as f:
            content = f.read()

        updated_count = 0
        for cid, slug in self.channels.items():
            new_key = self.get_m3u8_file(cid, slug)
            if new_key:
                # 这里的正则也要放宽，以适应新的长 Key
                # 找到 "key": "旧值" 并替换
                pattern = rf'"{cid}"\s*:\s*\{{[^}}]*?key\s*:\s*["\'][^"\']*["\']'
                replacement = f'"{cid}": {{ name: "", key: "{new_key}" }}'
                
                content = re.sub(pattern, replacement, content, flags=re.DOTALL)
                updated_count += 1
            
            time.sleep(10)

        if updated_count > 0:
            with open(self.worker_file, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"🚀 更新完成！写入了 {updated_count} 个新 Key。")
        else:
            print("💡 本次未更新。")

if __name__ == "__main__":
    OfiiiM3u8Hunter().run()
