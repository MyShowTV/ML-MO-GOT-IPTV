#!/usr/bin/env python3
"""
龙华频道 AssetID 自动抓取脚本
简化版 - 专门用于 GitHub Actions
"""

import os
import sys
import json
import time
import re
import logging
import requests
from datetime import datetime
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sync.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 代理设置
PROXY = os.environ.get('HTTPS_PROXY') or os.environ.get('HTTP_PROXY')

class LonghuaSync:
    def __init__(self):
        self.base_url = "https://www.ofiii.com/"
        self.session = requests.Session()
        
        # 请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7,zh-CN;q=0.6',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.ofiii.com/',
            'Connection': 'keep-alive',
        }
        
        # 设置代理
        if PROXY:
            self.session.proxies = {
                'http': PROXY,
                'https': PROXY
            }
            logger.info(f"使用代理: {PROXY}")
        
        # 龙华频道配置
        self.channels = {
            'lhtv01': {'name': '龙华电影', 'path': 'channel/movie'},
            'lhtv02': {'name': '龙华经典', 'path': 'channel/classic'},
            'lhtv03': {'name': '龙华戏剧', 'path': 'channel/drama'},
            'lhtv04': {'name': '龙华日韩', 'path': 'channel/japan-korea'},
            'lhtv05': {'name': '龙华偶像', 'path': 'channel/idol'},
            'lhtv06': {'name': '龙华卡通', 'path': 'channel/cartoon'},
            'lhtv07': {'name': '龙华洋片', 'path': 'channel/foreign'},
        }
    
    def test_proxy(self):
        """测试代理是否正常工作"""
        try:
            response = self.session.get('http://ip-api.com/json/', timeout=10)
            if response.status_code == 200:
                data = response.json()
                country = data.get('countryCode', 'Unknown')
                ip = data.get('query', 'Unknown')
                logger.info(f"代理测试: IP={ip}, 国家={country}")
                return country == 'TW'
        except Exception as e:
            logger.error(f"代理测试失败: {e}")
        return False
    
    def fetch_asset_id(self, channel_path):
        """抓取单个频道的 AssetID"""
        try:
            url = f"{self.base_url}{channel_path}"
            logger.info(f"抓取: {url}")
            
            response = self.session.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            content = response.text
            
            # 查找 AssetID 的多种模式
            patterns = [
                r'playlist/([a-zA-Z0-9_-]{10,})/master\.m3u8',
                r'assetId["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                r'"([a-zA-Z0-9_-]{10,20})"',  # 可能是 AssetID
                r'video/playlist/([^/]+)/',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    if len(match) >= 10 and match.isalnum():
                        logger.info(f"找到 AssetID: {match[:10]}...")
                        return match
            
            # 如果直接页面没找到，尝试查找可能的 API 请求
            api_patterns = [
                r'https?://[^"\']+\.ofiii\.com[^"\']+playlist[^"\']+',
                r'https?://[^"\']+\.ofiii\.com[^"\']+video[^"\']+',
            ]
            
            for pattern in api_patterns:
                matches = re.findall(pattern, content)
                for api_url in matches:
                    if 'playlist' in api_url and 'master.m3u8' in api_url:
                        match = re.search(r'playlist/([^/]+)/master\.m3u8', api_url)
                        if match:
                            asset_id = match.group(1)
                            logger.info(f"从API URL找到 AssetID: {asset_id[:10]}...")
                            return asset_id
            
            logger.warning("未找到 AssetID")
            return None
            
        except requests.RequestException as e:
            logger.error(f"请求失败: {e}")
            return None
        except Exception as e:
            logger.error(f"解析失败: {e}")
            return None
    
    def sync_all_channels(self):
        """同步所有频道"""
        results = {}
        success_count = 0
        
        logger.info("开始同步龙华频道...")
        
        for channel_id, channel_info in self.channels.items():
            logger.info(f"处理: {channel_info['name']}")
            
            asset_id = self.fetch_asset_id(channel_info['path'])
            
            if asset_id:
                results[channel_id] = {
                    'name': channel_info['name'],
                    'key': asset_id,
                    'type': 'ofiii',
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                success_count += 1
                logger.info(f"✅ {channel_info['name']}: 成功")
            else:
                results[channel_id] = {
                    'name': channel_info['name'],
                    'key': '这里填钥匙',  # 保持原样
                    'type': 'ofiii',
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'error': '未找到 AssetID'
                }
                logger.warning(f"❌ {channel_info['name']}: 失败")
            
            # 避免请求过快
            time.sleep(1)
        
        return results, success_count
    
    def update_workers_config(self, results):
        """更新 workers.js 配置文件"""
        try:
            workers_file = "workers.js"
            if not os.path.exists(workers_file):
                # 如果不存在，创建基本模板
                self.create_workers_template(workers_file)
            
            with open(workers_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            updated = False
            for channel_id, data in results.items():
                if data.get('key') and data['key'] != '这里填钥匙':
                    # 查找并替换配置
                    pattern = rf'"{channel_id}":\s*{{\s*name:\s*"[^"]+",\s*key:\s*"[^"]+"'
                    replacement = f'"{channel_id}": {{ name: "{data["name"]}", key: "{data["key"]}"'
                    
                    if re.search(pattern, content):
                        content = re.sub(pattern, replacement, content)
                        updated = True
                        logger.info(f"更新 {data['name']} 配置")
            
            if updated:
                # 备份原文件
                backup_file = f"workers.js.backup.{int(time.time())}"
                with open(backup_file, 'w', encoding='utf-8') as f:
                    with open(workers_file, 'r', encoding='utf-8') as original:
                        f.write(original.read())
                
                # 写入更新
                with open(workers_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                logger.info("✅ workers.js 已更新")
                return True
            
            logger.info("⚠️ 没有需要更新的配置")
            return False
            
        except Exception as e:
            logger.error(f"更新配置文件失败: {e}")
            return False
    
    def create_workers_template(self, filename):
        """创建 workers.js 模板（如果不存在）"""
        template = """export default {
  async fetch(request) {
    const url = new URL(request.url);
    const host = url.host;
    const path = url.pathname.replace(/^\/|\\.m3u8$/gi, "").toLowerCase();
    const UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36";

    const config = {
      "lhtv01": { name: "龙华电影", key: "这里填钥匙", type: "ofiii" },
      "lhtv02": { name: "龙华经典", key: "这里填钥匙", type: "ofiii" },
      "lhtv03": { name: "龙华戏剧", key: "这里填钥匙", type: "ofiii" },
      "lhtv04": { name: "龙华日韩", key: "这里填钥匙", type: "ofiii" },
      "lhtv05": { name: "龙华偶像", key: "这里填钥匙", type: "ofiii" },
      "lhtv06": { name: "龙华卡通", key: "这里填钥匙", type: "ofiii" },
      "lhtv07": { name: "龙华洋片", key: "这里填钥匙", type: "ofiii" }
    };

    if (path === "" || path === "index") {
      let html = `<html><head><meta charset="utf-8"><title>电视直播源</title></head><body><h1>📺 龙华频道</h1>`;
      for (const id in config) {
        html += `<div><a href="https://${host}/${id}.m3u8">${config[id].name}</a></div>`;
      }
      return new Response(html, { headers: { "Content-Type": "text/html;charset=UTF-8" } });
    }

    const ch = config[path];
    if (!ch) return new Response("404", { status: 404 });

    if (ch.type === "ofiii") {
      if (ch.key === "这里填钥匙") return new Response("AssetID 未更新", { status: 500 });
      
      const finalUrl = `https://cdi.ofiii.com/ocean/video/playlist/${ch.key}/master.m3u8`;
      const res = await fetch(finalUrl, { headers: { "Referer": "https://www.ofiii.com/", "User-Agent": UA } });
      
      if (!res.ok) return new Response("钥匙失效", { status: 403 });
      
      let content = await res.text();
      const baseUrl = finalUrl.substring(0, finalUrl.lastIndexOf('/') + 1);
      const fixedContent = content.split('\\n').map(line => {
        line = line.trim();
        if (line && !line.startsWith('#') && !line.startsWith('http')) return baseUrl + line;
        return line;
      }).join('\\n');
      
      return new Response(fixedContent, { 
        headers: { 
          "Content-Type": "application/vnd.apple.mpegurl", 
          "Access-Control-Allow-Origin": "*" 
        } 
      });
    }
    
    return new Response("未找到频道", { status: 404 });
  }
};
"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(template)
        logger.info(f"创建 workers.js 模板: {filename}")
    
    def save_results(self, results):
        """保存结果到 JSON 文件"""
        timestamp = int(time.time())
        filename = f"longhua_assets_{timestamp}.json"
        
        data = {
            'timestamp': timestamp,
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'channels': results
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"结果保存到: {filename}")
            return filename
        except Exception as e:
            logger.error(f"保存结果失败: {e}")
            return None

def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("龙华频道 AssetID 同步开始")
    logger.info("=" * 50)
    
    syncer = LonghuaSync()
    
    # 测试代理
    if PROXY:
        logger.info("测试代理连接...")
        if not syncer.test_proxy():
            logger.error("❌ 代理测试失败，请确保使用台湾IP")
            return False
    else:
        logger.warning("⚠️ 未设置代理，可能无法访问")
    
    # 同步频道
    results, success_count = syncer.sync_all_channels()
    
    # 显示结果
    logger.info("=" * 50)
    logger.info(f"同步完成: {success_count}/{len(syncer.channels)} 成功")
    logger.info("=" * 50)
    
    # 保存结果
    json_file = syncer.save_results(results)
    
    # 更新 workers.js
    if success_count > 0:
        logger.info("更新 workers.js...")
        syncer.update_workers_config(results)
    else:
        logger.warning("没有成功抓取到 AssetID，跳过更新")
    
    # 显示摘要
    logger.info("结果摘要:")
    for channel_id, data in results.items():
        status = "✅" if data.get('key') and data['key'] != '这里填钥匙' else "❌"
        key_preview = data['key'][:10] + "..." if len(data['key']) > 10 else data['key']
        logger.info(f"  {status} {data['name']}: {key_preview}")
    
    logger.info("=" * 50)
    
    # 返回是否成功
    return success_count > 0

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"脚本执行失败: {e}")
        sys.exit(1)
