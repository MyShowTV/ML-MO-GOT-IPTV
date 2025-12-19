import os
import re
import time
import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def get_asset_id_final(cid, slug):
    print(f"🔍 正在抓取頻道: {cid} (Slug: {slug})...")
    chromedriver_autoinstaller.install()
    
    options = Options()
    # 使用 headless=new 是雲端抓取的關鍵，它更像真實瀏覽器
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    
    # --- 關鍵偽裝：把雲端環境偽裝成你本地的 Chrome ---
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--proxy-server=http://127.0.0.1:7890')

    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        
        # 抹除 WebDriver 特徵（防止被 Ofiii 拒絕訪問）
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })
        
        driver.set_page_load_timeout(45)
        driver.get(f"https://www.ofiii.com/channel/watch/{slug}")
        
        # 模仿你本地的操作：給予充足的渲染時間
        print(f"⏳ 等待 15 秒讓網頁數據完全加載...")
        time.sleep(15) 

        html = driver.page_source
        
        # 使用你本地測試成功的正則表達式
        match = re.search(r'"assetId"\s*:\s*"([a-zA-Z0-9_-]+)"', html)
        
        if match:
            aid = match.group(1)
            print(f"✅ 【同步成功】 {cid} -> {aid}")
            return aid
        else:
            # 如果失敗，嘗試從 Next.js 專用的 JSON 區塊提取
            print(f"⚠️ 常規匹配失敗，嘗試深度解析 JSON 區塊...")
            next_match = re.search(r'id="__NEXT_DATA__".*?>(.*?)</script>', html)
            if next_match:
                aid_in_json = re.search(r'"assetId"\s*:\s*"([a-zA-Z0-9_-]+)"', next_match.group(1))
                if aid_in_json:
                    return aid_in_json.group(1)
            
            print(f"❌ {cid} 抓取失敗。")
    except Exception as e:
        print(f"🔥 {cid} 發生異常: {e}")
    finally:
        if driver:
            driver.quit()
    return None

def main():
    # 完整的 7 個頻道對應
    channels = {
        'lhtv01': 'litv-longturn03', # 龍華電影
        'lhtv02': 'litv-longturn21', # 龍華經典
        'lhtv03': 'litv-longturn18', # 龍華戲劇
        'lhtv04': 'litv-longturn11', # 龍華日韓
        'lhtv05': 'litv-longturn12', # 龍華偶像
        'lhtv06': 'litv-longturn01', # 龍華卡通
        'lhtv07': 'litv-longturn02', # 龍華洋片
    }
    
    workers_file = "workers.js"
    if not os.path.exists(workers_file):
        print(f"❌ 找不到 {workers_file}，請確認文件在同級目錄下")
        return
        
    with open(workers_file, "r", encoding="utf-8") as f:
        content = f.read()

    any_updated = False
    for cid, slug in channels.items():
        aid = get_asset_id_final(cid, slug)
        if aid:
            # 正則替換 workers.js 中的 key 欄位
            pattern = rf'"{cid}"\s*:\s*\{{[^}}]*?key\s*:\s*["\'][^"\']*["\']'
            replacement = f'"{cid}": {{ name: "", key: "{aid}" }}'
            
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                any_updated = True
        time.sleep(3) # 頻道間隔

    if any_updated:
        with open(workers_file, "w", encoding="utf-8") as f:
            f.write(content)
        print("🚀 [SUCCESS] 所有頻道鑰匙已更新至 workers.js")
    else:
        print("😭 未能捕獲任何有效數據，請檢查代理或 Slug 是否正確。")

if __name__ == "__main__":
    main()
