import os, re, time
import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def get_asset_id_final(cid, slug):
    print(f"🔍 正在抓取頻道: {cid}...")
    chromedriver_autoinstaller.install()
    
    options = Options()
    # 关键：使用新的无头模式，这比旧的 --headless 更难被发现
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument(f'--proxy-server=http://127.0.0.1:7890')
    
    # 注入一个看起来非常真实的 User-Agent
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    options.add_argument(f'user-agent={ua}')

    # 禁用被自动化工具控制的特征
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        
        # 核心：通过 CDP 协议在页面加载前强行删除 webdriver 特征
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                window.chrome = { runtime: {} };
            """
        })

        driver.set_page_load_timeout(60)
        # 直接访问 API 数据接口或渲染后的页面
        driver.get(f"https://www.ofiii.com/channel/watch/{slug}")
        
        # 增加等待时间，确保 Next.js 数据块渲染完成
        time.sleep(25) 

        html = driver.page_source
        
        # 你的本地成功正则逻辑
        match = re.search(r'"assetId"\s*:\s*"([a-zA-Z0-9_-]+)"', html)
        
        if match:
            aid = match.group(1)
            print(f"🎯 【成功捕获】 {cid} -> {aid}")
            return aid
        
        # 备选：如果没有直接匹配到，尝试搜索脚本内的 JSON
        print(f"⚠️ {cid} 常规匹配失败，检查源码长度: {len(html)}")
        if len(html) < 5000:
            print(f"❌ 源码过短，可能被拦截。")

    except Exception as e:
        print(f"🔥 {cid} 异常: {e}")
    finally:
        if driver: driver.quit()
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
