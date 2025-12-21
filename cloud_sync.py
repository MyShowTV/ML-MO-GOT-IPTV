import os, re, time, requests, json, urllib3
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class OfiiiNetworkSniffer:
    def __init__(self):
        self.proxy_host = "brd.superproxy.io:33335"
        self.proxy_user = "brd-customer-hl_739668d7-zone-residential_proxy1-country-tw"
        self.proxy_pass = "me6lrg0ysg96"
        
        self.worker_file = "workers.js"
        self.channels = {'lhtv01': 'litv-longturn03'} # 先拿一个频道测试

    def get_key_via_network_logs(self, cid, slug):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🚨 启动深度网络嗅探: {cid}")
        
        proxy_url = f"http://{self.proxy_user}:{self.proxy_pass}@{self.proxy_host}"
        proxies = {"http": proxy_url, "https": proxy_url}
        
        # 核心：使用 x-brd-network 指令，这会要求代理返回所有网络请求的 JSON 列表
        headers = {
            "x-api-render": "true",
            "x-api-actions": json.dumps([
                {"wait": ".vjs-big-play-button"},
                {"click": ".vjs-big-play-button"},
                {"wait": 15000} # 必须等待，让 m3u8 请求发出来
            ]),
            "x-brd-network": "true" # 强制开启网络包嗅探
        }

        try:
            url = f"https://www.ofiii.com/channel/watch/{slug}"
            response = requests.get(url, proxies=proxies, headers=headers, timeout=180, verify=False)
            
            # Bright Data 会在 response body 或 header 中提供网络请求日志
            # 如果配置正确，这些 URL 会直接出现在文本中
            content = response.text
            
            # 搜索包含 /playlist/ 的链接
            # 这次我们找得更宽泛，只要包含 playlist 且以 m3u8 结尾
            finds = re.findall(r'https?://[^\s"\'<>]+playlist/[^\s"\'<>]+m3u8', content)
            
            if finds:
                # 排除报错的链接，找最复杂的那个
                for raw_url in finds:
                    if "avc1" in raw_url:
                        # 提取 /playlist/ 之后的部分
                        match = re.search(r'playlist/([a-zA-Z0-9_-]+/[^"\'\s]+\.m3u8)', raw_url)
                        if match:
                            result = match.group(1)
                            print(f"✅ 嗅探成功！发现真实路径: {result}")
                            return result
            
            # 如果上面没找到，打印一下 response 里的所有 URL 看看
            print("⚠️ 未发现直接链接，正在扫描所有潜在请求...")
            all_urls = re.findall(r'https?://[^\s"\'<>]+', content)
            for u in all_urls:
                if "m3u8" in u:
                    print(f"🔎 发现可疑 M3U8: {u}")
                    
        except Exception as e:
            print(f"🔥 嗅探异常: {e}")
        return None

if __name__ == "__main__":
    sniffer = OfiiiNetworkSniffer()
    sniffer.get_key_via_network_logs('lhtv01', 'litv-longturn03')
