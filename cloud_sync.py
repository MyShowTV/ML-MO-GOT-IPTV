#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
龙华频道 AssetID 自动抓取脚本（优化版）
适配新版 ofiii 页面结构 + 自动重试机制 + 保留原兼容逻辑
"""

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

        # Headers
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.ofiii.com/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
        }

        if PROXY:
            self.session.proxies = {"http": PROXY, "https": PROXY}
            logger.info(f"使用代理: {PROXY}")

        # ✅ 修正版频道路径
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
        """检测代理是否来自台湾"""
        try:
            resp = self.session.get("http://ip-api.com/json/", timeout=10)
            data = resp.json()
            logger.info(f"代理测试: IP={data.get('query')}, 国家={data.get('countryCode')}")
            return data.get("countryCode") == "TW"
        except Exception as e:
            logger.error(f"代理测试失败: {e}")
            return False

    def fetch_asset_id(self, url, retries=3):
        """抓取单频道 AssetID，自动重试"""
        for attempt in range(1, retries + 1):
            try:
                logger.info(f"📡 请求 ({attempt}/{retries}): {url}")
                res = self.session.get(url, headers=self.headers, timeout=15)
                res.raise_for_status()
                html = res.text

                # 尝试匹配新版播放地址格式
                patterns = [
                    r"playlist/([a-zA-Z0-9_-]{10,})/master\.m3u8",
                    r'asset[Ii]d["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                    r'"asset_id"\s*:\s*"([^"]+)"',
                ]
                for p in patterns:
                    match = re.search(p, html)
                    if match:
                        asset_id = match.group(1)
                        logger.info(f"✅ 找到 AssetID: {asset_id}")
                        return asset_id

                # 没找到，警告
                logger.warning(f"⚠️ 页面中未找到 AssetID (尝试 {attempt})")
                time.sleep(2)

            except requests.RequestException as e:
                logger.error(f"请求失败 ({attempt}/{retries}): {e}")
                time.sleep(2)

        return None

    def sync_all_channels(self):
        results = {}
        success = 0

        logger.info("=" * 50)
        logger.info("开始同步龙华频道...")
        logger.info("=" * 50)

        for cid, info in self.channels.items():
            url = f"{self.base_url}{info['path']}"
            logger.info(f"▶️ 抓取 {info['name']} ...")
            asset_id = self.fetch_asset_id(url)

            if asset_id:
                results[cid] = {
                    "name": info["name"],
                    "key": asset_id,
                    "type": "ofiii",
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
                logger.info(f"✅ 成功：{info['name']}")
                success += 1
            else:
                results[cid] = {
                    "name": info["name"],
                    "key": "这里填钥匙",
                    "type": "ofiii",
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "error": "未找到 AssetID",
                }
                logger.warning(f"❌ 失败：{info['name']}")

            time.sleep(1)

        return results, success

    def save_results(self, results):
        filename = f"longhua_assets_{int(time.time())}.json"
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump({
                    "timestamp": int(time.time()),
                    "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "channels": results
                }, f, ensure_ascii=False, indent=2)
            logger.info(f"💾 结果保存到: {filename}")
            return filename
        except Exception as e:
            logger.error(f"保存失败: {e}")
            return None

    def update_workers_config(self, results):
        """更新 workers.js 文件"""
        try:
            workers = "workers.js"
            if not os.path.exists(workers):
                self.create_workers_template(workers)

            with open(workers, "r", encoding="utf-8") as f:
                content = f.read()

            updated = False
            for cid, data in results.items():
                if data["key"] != "这里填钥匙":
                    pattern = rf'"{cid}":\s*{{\s*name:\s*"[^"]+",\s*key:\s*"[^"]+"'
                    replacement = f'"{cid}": {{ name: "{data["name"]}", key: "{data["key"]}"'
                    if re.search(pattern, content):
                        content = re.sub(pattern, replacement, content)
                        updated = True
                        logger.info(f"🔄 更新 {data['name']}")

            if updated:
                with open(workers, "w", encoding="utf-8") as f:
                    f.write(content)
                logger.info("✅ workers.js 已更新")
            else:
                logger.info("⚠️ 无需更新配置")

        except Exception as e:
            logger.error(f"更新配置失败: {e}")

    def create_workers_template(self, filename):
        """生成 workers.js 模板"""
        template = """export default {
  async fetch(request) {
    const url = new URL(request.url);
    const path = url.pathname.replace(/^\\/|\\.m3u8$/gi, '').toLowerCase();

    const config = {
      "lhtv01": { name: "龙华电影", key: "这里填钥匙", type: "ofiii" },
      "lhtv02": { name: "龙华经典", key: "这里填钥匙", type: "ofiii" },
      "lhtv03": { name: "龙华戏剧", key: "这里填钥匙", type: "ofiii" },
      "lhtv04": { name: "龙华日韩", key: "这里填钥匙", type: "ofiii" },
      "lhtv05": { name: "龙华偶像", key: "这里填钥匙", type: "ofiii" },
      "lhtv06": { name: "龙华卡通", key: "这里填钥匙", type: "ofiii" },
      "lhtv07": { name: "龙华洋片", key: "这里填钥匙", type: "ofiii" }
    };

    const ch = config[path];
    if (!ch) return new Response("404 Not Found", { status: 404 });
    if (ch.key === "这里填钥匙") return new Response("AssetID 未更新", { status: 500 });

    const m3u8 = `https://cdi.ofiii.com/ocean/video/playlist/${ch.key}/master.m3u8`;
    const res = await fetch(m3u8, { headers: { "Referer": "https://www.ofiii.com/" } });
    const text = await res.text();
    return new Response(text, {
      headers: { "Content-Type": "application/vnd.apple.mpegurl", "Access-Control-Allow-Origin": "*" }
    });
  }
};
"""
        with open(filename, "w", encoding="utf-8") as f:
            f.write(template)
        logger.info("🧩 已创建 workers.js 模板")



def main():
    logger.info("=" * 50)
    logger.info("龙华频道 AssetID 同步开始")
    logger.info("=" * 50)

    syncer = LonghuaSync()

    if PROXY:
        if not syncer.test_proxy():
            logger.error("❌ 代理测试失败，请使用台湾节点")
            return False
    else:
        logger.warning("⚠️ 未设置代理，可能无法访问台湾资源")

    results, success = syncer.sync_all_channels()
    syncer.save_results(results)

    if success > 0:
        syncer.update_workers_config(results)
    else:
        logger.warning("❌ 未抓取到任何有效 AssetID")

    logger.info("=" * 50)
    logger.info(f"同步完成: {success}/{len(syncer.channels)} 成功")
    logger.info("=" * 50)
    return success > 0


if __name__ == "__main__":
    try:
        ok = main()
        sys.exit(0 if ok else 1)
    except Exception as e:
        logger.error(f"执行失败: {e}")
        sys.exit(1)
