import os, re, time, requests, json, urllib3
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class OfiiiUltimatePro:
    def __init__(self):
        # 你的住宅代理凭据
        self.proxy_host = "brd.superproxy.io:33335"
        self.proxy_user = "brd-customer-hl_739668d7-zone-residential_proxy1-country-tw"
        self.proxy_pass = "me6lrg0ysg96"
        
        self.worker_file = "workers.js"
        # 目标频道
        self.target = {'cid': 'lhtv01', 'slug': 'litv-longturn03'}

    def sniffer(self):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 启动真机级拦截: {self.target['cid']}")
        
        proxy_url = f"http://{self.proxy_user}:{self.proxy_pass}@{self.proxy_host}"
        proxies = {"http": proxy_url, "https": proxy_url}
        
        # --- 核心配置：完全模拟真实用户行为 ---
        headers = {
            # 1. 开启高级渲染和浏览器指纹模拟
            "x-api-render": "true",
            "x-api-device": "desktop",
            "x-api-browser": "chrome",
            # 2. 模拟真实操作序列
            "x-api-actions": json.dumps([
                {"scroll_to": "window.innerHeight / 2"}, # 模拟滚动
                {"wait": ".video-player"}, 
                {"click": ".vjs-big-play-button"},      # 触发播放
                {"wait": 20000}                         # 关键：必须留足时间加载真正的 m3u8
            ]),
            # 3. 强制要求 Bright Data 返回完整的网络日志列表
            "x-brd-network": "true",
            "Accept": "application/json"
        }

        try:
            url = f"https://www.ofiii.com/channel/watch/{self.target['slug']}"
            # 我们请求的其实是 Bright Data 的渲染节点
            response = requests.get(url, proxies=proxies, headers=headers, timeout=240, verify=False)
            
            # 解析返回的日志。Bright Data 的网络拦截模式会返回一个包含所有 URL 的内容
            log_data = response.text
            
            print(f"📄 流量嗅探完成，分析中... (数据量: {len(log_data)} 字节)")

            # --- 模式匹配：寻找你提到的 playlist 结构 ---
            # 模式 1: 标准 playlist 路径
            # 模式 2: 包含 avc1 的复杂链接
            # 模式 3: 包含 .m3u8 的任意路径
            patterns = [
                r'https?://[^\s"\'<>]+playlist/[a-zA-Z0-9_-]+/[^\s"\'<>]+\.m3u8',
                r'/playlist/[a-zA-Z0-9_-]+/[^\s"\'<>]+\.m3u8',
                r'https?://[^\s"\'<>]+litv[^\s"\'<>]*?\.m3u8'
            ]
            
            found_urls = []
            for p in patterns:
                found_urls.extend(re.findall(p, log_data))
            
            # 去重并筛选
            valid_keys = []
            if found_urls:
                print("\n--- 🕵️‍♂️ 拦截到的关键流量 ---")
                for u in set(found_urls):
                    # 提取你提到的那个“密匙/文件名”结构
                    if "/playlist/" in u:
                        match = re.search(r'playlist/([a-zA-Z0-9_-]+/[^"\'\s]+\.m3u8)', u)
                        if match:
                            key = match.group(1)
                            valid_keys.append(key)
                            print(f"🎯 命中！Key: {key}")
                    else:
                        print(f"🔗 发现相关流: {u}")
            
            if not valid_keys:
                print("❌ 拦截失败。可能原因：1. 广告未跑完 2. 住宅 IP 被识别 3. 页面未正确触发点击")
                # 最后的倔强：搜索所有包含 "avc1" 的字符串
                if "avc1" in log_data:
                    print("⚠️ 警告：流量中确实出现了 avc1，但正则解析失败，正在尝试强行提取...")
                    # 强行提取 avc1 周边的字符串
                    raw_hits = re.findall(r'([a-zA-Z0-9_-]+/litv-longturn[^\s"\'<>]+avc1[^\s"\'<>]+)', log_data)
                    for hit in raw_hits:
                        print(f"🔍 强行捕获: {hit}")

        except Exception as e:
            print(f"🔥 系统崩溃: {e}")

if __name__ == "__main__":
    OfiiiUltimatePro().sniffer()
