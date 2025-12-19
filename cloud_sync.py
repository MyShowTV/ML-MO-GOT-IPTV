#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import re
import time
import logging
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)

# --- 关键衔接配置 ---
WORKERS_URL = "https://你的域名.workers.dev/update_key" # ⚠️ 必须修改
AUTH_PASSWORD = "your_password_666"                   # ⚠️ 与 Workers 保持一致
PROXY = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")

class LonghuaSync:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.ofiii.com/"
        }
        if PROXY:
            self.session.proxies = {"http": PROXY, "https": PROXY}
            logger.info(f"🚀 代理已挂载: {PROXY}")

        # 这里的 key 必须与 Workers 的 config[id] 对应
        self.channels = {
            'litv-longturn03': 'channel/watch/litv-longturn03', # 电影
            'litv-longturn21': 'channel/watch/litv-longturn05', # 经典
            'litv-longturn18': 'channel/watch/litv-longturn02', # 戏剧
            'litv-longturn11': 'channel/watch/litv-longturn04', # 日韩
            'litv-longturn12': 'channel/watch/litv-longturn01', # 偶像
            'litv-longturn01': 'channel/watch/litv-longturn06', # 卡通
            'litv-longturn02': 'channel/watch/litv-longturn07', # 洋片
        }

    def fetch_id(self, path):
        url = f"https://www.ofiii.com/{path}"
        try:
            res = self.session.get(url, headers=self.headers, timeout=15)
            match = re.search(r"playlist/([a-zA-Z0-9_-]{8,})/master\.m3u8", res.text)
            return match.group(1) if match else None
        except Exception as e:
            logger.error(f"抓取出错 {path}: {e}")
            return None

    def push(self, cid, key):
        payload = {"id": cid, "key": key, "pw": AUTH_PASSWORD}
        try:
            # 推送时禁用代理，直连 Cloudflare
            r = requests.post(WORKERS_URL, json=payload, timeout=10, proxies={"http": None, "https": None})
            logger.info(f"📤 推送 {cid} {'成功' if r.status_code==200 else '失败'}")
        except Exception as e:
            logger.error(f"🔥 推送异常: {e}")

    def run(self):
        for cid, path in self.channels.items():
            asset_id = self.fetch_id(path)
            if asset_id: self.push(cid, asset_id)
            time.sleep(1)

if __name__ == "__main__":
    LonghuaSync().run()
