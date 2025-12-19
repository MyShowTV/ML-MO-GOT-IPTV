import os, re, time
import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_asset_id_advanced(cid, slug):
    print(f"🔍 正在深度解析频道: {cid} (Slug: {slug})...")
    chromedriver_autoinstaller.install()
    
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    # 核心：伪装真实浏览器，防止被识别为爬虫
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    options.add_argument('--proxy-server=http://127.0.0.1:7890')

    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        # 执行 CDP 命令进一步隐藏特征
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })
        
        driver.set_page_load_timeout(45)
        driver.get(f"https://www.ofiii.com/channel/watch/{slug}")
        
        # 显式等待：直到 Next.js 的核心数据脚本标签出现在 DOM 中
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, "__NEXT_DATA__"))
            )
        except:
            print(f"⚠️ {cid} 等待超时，尝试直接解析源码...")

        html = driver.page_source
        
        # 方案 A：从 Next.js 的静态 JSON 块中提取（最稳）
        next_data = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html)
        if next_data:
            json_str = next_data.group(1)
            aid_match = re.search(r'"assetId"\s*:\s*"([a-zA-Z0-9_-]+)"', json_str)
            if aid_match:
                aid = aid_match.group(1)
                print(f"🎯 【精准命中】 {cid} -> {aid}")
                return aid

        # 方案 B：全局正则匹配
        aid_match = re.search(r'"assetId"\s*:\s*"([a-zA-Z0-9_-]+)"', html)
        if aid_match:
            aid = aid_match.group(1)
            print(f"✅ 【正则捕获】 {cid} -> {aid}")
            return aid

        print(f"❌ {cid} 抓取失败：页面可能未正常渲染或地区限制")
    except Exception as e:
        print(f"🔥 {cid} 运行异常: {e}")
    finally:
        if driver: driver.quit()
    return None

def main():
    # lhtv01 到 lhtv07 全频道对应表
    channels = {
        'lhtv01': 'litv-longturn03', # 龙华电影
        'lhtv02': 'litv-longturn21', # 龙华经典
        'lhtv03': 'litv-longturn18', # 龙华戏剧
        'lhtv04': 'litv-longturn11', # 龙华日韩
        'lhtv05': 'litv-longturn12', # 龙华偶像
        'lhtv06': 'litv-longturn01', # 龙华卡通
        'lhtv07': 'litv-longturn02', # 龙华洋片
    }
    
    workers_file = "workers.js"
    if not os.path.exists(workers_file):
        print(f"❌ 错误: 找不到 {workers_file}")
        return
        
    with open(workers_file, "r", encoding="utf-8") as f:
        content = f.read()

    any_updated = False
    for cid, slug in channels.items():
        aid = get_asset_id_advanced(cid, slug)
        if aid:
            # 这里的正则要匹配 workers.js 中的格式，例如 "lhtv01": { name: "", key: "..." }
            pattern = rf'"{cid}"\s*:\s*\{{[^}}]*?key\s*:\s*["\'][^"\']*["\']'
            replacement = f'"{cid}": {{ name: "", key: "{aid}" }}'
            
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                any_updated = True
        time.sleep(3) # 减缓压力

    if any_updated:
        with open(workers_file, "w", encoding="utf-8") as f:
            f.write(content)
        print("🚀 [SUCCESS] 所有频道钥匙已同步至 workers.js")
    else:
        print("😭 未能捕获任何有效数据，请检查台湾代理节点。")

if __name__ == "__main__":
    main()
