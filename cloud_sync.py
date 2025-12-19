#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import re
import json
import time
import logging
import requests
from datetime import datetime

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("sync.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

PROXY = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")

class LonghuaSync:
    def __init__(self):
        self.base_url = "https://www.ofiii.com/"
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.ofiii.com/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
            "X-Requested-With": "XMLHttpRequest"
        }

        if PROXY:
            self.session.proxies = {"http": PROXY, "https": PROXY}
            logger.info(f"🚀 已挂载代理: {PROXY}")

        self.channels = {
            'lhtv01': {'name': '龙华电影', 'path': 'channel/watch/litv-longturn03'},
            'lhtv02': {'name': '龙华经典', 'path': 'channel/watch/litv-longturn05'},
            'lhtv03': {'name': '龙华戏剧', 'path': 'channel/watch/litv-longturn02'},
            'lhtv04': {'name': '龙华日韩', 'path': 'channel/watch/litv-longturn04'},
            'lhtv05': {'name': '龙华偶像', 'path': 'channel/watch/litv-longturn01'},
            'lhtv06': {'name': '龙华卡通', 'path': 'channel/watch/litv-longturn06'},
            'lhtv07': {'name': '龙华洋片', 'path': 'channel/watch/litv-longturn07'},
        }

    def test_proxy(self):
        try:
            resp = self.session.get("http://ip-api.com/json/", timeout=10)
            data = resp.json()
            logger.info(f"🌐 代理测试: IP={data.get('query')}, 国家={data.get('countryCode')}")
            return data.get("countryCode") == "TW"
        except Exception as e:
            logger.error(f"❌ 代理连接失败: {e}")
            return False

    def fetch_asset_id(self, url, retries=3):
        for attempt in range(1, retries + 1):
            try:
                res = self.session.get(url, headers=self.headers, timeout=15)
                res.raise_for_status()
                html = res.text
                patterns = [
                    r"playlist/([a-zA-Z0-9_-]{8,})/master\.m3u8",
                    r'asset[Ii]d["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                    r'"asset_id"\s*:\s*"([^"]+)"',
                ]
                for p in patterns:
                    match = re.search(p, html)
                    if match:
                        return match.group(1)
                time.sleep(2)
            except Exception as e:
                logger.error(f"❌ 请求出错 ({attempt}/{retries}): {e}")
                time.sleep(2)
        return None

    def update_workers_config(self, results):
        workers = "workers.js"
        if not os.path.exists(workers):
            self.create_workers_template(workers)
        with open(workers, "r", encoding="utf-8") as f:
            content = f.read()
        updated_count = 0
        for cid, data in results.items():
            if data["key"] and data["key"] != "这里填钥匙":
                pattern = rf'("{cid}":\s*\{{[^}}]*key:\s*")([^"]*)(")'
                if re.search(pattern, content):
                    content = re.sub(pattern, rf'\g<1>{data["key"]}\g<3>', content, flags=re.DOTALL)
                    updated_count += 1
                    logger.info(f"🔄 已同步: {data['name']} -> {data['key']}")
        if updated_count > 0:
            with open(workers, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"✅ workers.js 更新成功")

    def create_workers_template(self, filename):
        template = """export default {
  async fetch(request) {
    const url = new URL(request.url);
    const path = url.pathname.replace(/^\/|\.m3u8$/gi, '').toLowerCase();
    const config = {
      "lhtv01": { name: "龙华电影", key: "这里填钥匙" },
      "lhtv02": { name: "龙华经典", key: "这里填钥匙" },
      "lhtv03": { name: "龙华戏剧", key: "这里填钥匙" },
      "lhtv04": { name: "龙华日韩", key: "这里填钥匙" },
      "lhtv05": { name: "龙华偶像", key: "这里填钥匙" },
      "lhtv06": { name: "龙华卡通", key: "这里填钥匙" },
      "lhtv07": { name: "龙华洋片", key: "这里填钥匙" }
    };
    const ch = config[path];
    if (!ch || ch.key === "这里填钥匙") return new Response("404", { status: 404 });
    const m3u8 = `https://cdi.ofiii.com/ocean/video/playlist/${ch.key}/master.m3u8`;
    const res = await fetch(m3u8, { headers: { "Referer": "https://www.ofiii.com/" } });
    return new Response(await res.text(), {
      headers: { "Content-Type": "application/vnd.apple.mpegurl", "Access-Control-Allow-Origin": "*" }
    });
  }
};"""
        with open(filename, "w", encoding="utf-8") as f:
            f.write(template)

    def run(self):
        if PROXY and not self.test_proxy():
            logger.error("❌ 代理检测不通过")
            return False
        results = {}
        success = 0
        for cid, info in self.channels.items():
            asset_id = self.fetch_asset_id(f"{self.base_url}{info['path']}")
            results[cid] = {"name": info["name"], "key": asset_id or "这里填钥匙"}
            if asset_id: success += 1
        if success > 0:
            self.update_workers_config(results)
        return success > 0

if __name__ == "__main__":
    sys.exit(0 if LonghuaSync().run() else 1)
