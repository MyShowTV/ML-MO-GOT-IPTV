import os
import re
import time
import requests
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)

class LonghuaSync:
    def __init__(self):
        # 必须使用环境变量中的代理，否则在 GitHub 环境无法访问台湾网站
        self.proxy = os.environ.get("HTTP_PROXY") or os.environ.get("HTTPS_PROXY")
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.ofiii.com/"
        }
        # 映射表：Workers 里的配置 ID : 网页抓取路径
        self.channels = {
            'lhtv01': 'channel/watch/litv-longturn03',
            'lhtv02': 'channel/watch/litv-longturn05',
            'lhtv03': 'channel/watch/litv-longturn02',
            'lhtv04': 'channel/watch/litv-longturn04',
            'lhtv05': 'channel/watch/litv-longturn01',
            'lhtv06': 'channel/watch/litv-longturn06',
            'lhtv07': 'channel/watch/litv-longturn07',
        }

    def fetch_id(self, path):
        url = f"https://www.ofiii.com/{path}"
        try:
            proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
            res = requests.get(url, headers=self.headers, proxies=proxies, timeout=15)
            match = re.search(r"playlist/([a-zA-Z0-9_-]{8,})/master\.m3u8", res.text)
            return match.group(1) if match else None
        except Exception as e:
            logger.error(f"抓取失败 {path}: {e}")
            return None

    def update_workers_file(self, results):
        """精准正则替换 workers.js 里的 key"""
        if not results: return
        with open("workers.js", "r", encoding="utf-8") as f:
            content = f.read()
        
        for cid, key in results.items():
            # 这里的正则匹配: "lhtv01": { ..., key: "旧钥匙" }
            # 仅替换 key: "..." 部分
            pattern = rf'("{cid}":\s*\{{[^}}]*key:\s*")([^"]*)(")'
            content = re.sub(pattern, rf'\1{key}\3', content, flags=re.DOTALL)
            
        with open("workers.js", "w", encoding="utf-8") as f:
            f.write(content)
        logger.info("✅ workers.js 文件已更新")

    def run(self):
        results = {}
        for cid, path in self.channels.items():
            logger.info(f"正在处理: {cid}")
            key = self.fetch_id(path)
            if key:
                results[cid] = key
                logger.info(f"成功获取 {cid}: {key}")
            time.sleep(1)
        self.update_workers_file(results)

if __name__ == "__main__":
    LonghuaSync().run()
