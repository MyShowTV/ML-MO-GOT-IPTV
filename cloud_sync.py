import os, re, time, json
import chromedriver_autoinstaller
from selenium import webdriver  # 注意：这里改回原生的 selenium，更轻量
from selenium.webdriver.chrome.options import Options

def get_asset_id_static(cid, slug):
    print(f"🔍 正在静态解析频道: {cid}...")
    chromedriver_autoinstaller.install()
    
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    # 依然需要代理，因为 Ofiii 限制台湾 IP 访问
    options.add_argument('--proxy-server=http://127.0.0.1:7890')

    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(30)
        
        # 访问页面
        driver.get(f"https://www.ofiii.com/channel/watch/{slug}")
        time.sleep(8) # 等待页面基础数据渲染完毕

        # 获取网页源代码
        html_source = driver.page_source

        # 核心逻辑：从 __NEXT_DATA__ 或 assetId 字段中提取
        # 匹配格式示例: "assetId":"B8KQyHS-600"
        match = re.search(r'"assetId"\s*:\s*"([a-zA-Z0-9_-]+)"', html_source)
        
        if match:
            aid = match.group(1)
            print(f"🎯 【解析成功】 {cid}: {aid}")
            return aid
        
        # 备选逻辑：查找可能是加密后的 ID 路径
        match = re.search(r'/playlist/([a-zA-Z0-9_-]+)/master\.m3u8', html_source)
        if match:
            aid = match.group(1)
            print(f"🎯 【路径提取成功】 {cid}: {aid}")
            return aid

        print(f"❌ {cid} 解析失败：源码中未找到 assetId")
    except Exception as e:
        print(f"🔥 {cid} 运行时异常: {e}")
    finally:
        if driver: driver.quit()
    return None

def main():
    channels = {
        'lhtv01': 'litv-longturn03',
        'lhtv03': 'litv-longturn02',
        'lhtv05': 'ofiii73',
        'lhtv06': 'ofiii74',
        'lhtv07': 'ofiii76',
    }
    
    workers_file = "workers.js"
    if not os.path.exists(workers_file):
        print("❌ 错误: 找不到 workers.js")
        return
        
    with open(workers_file, "r", encoding="utf-8") as f:
        content = f.read()

    any_updated = False
    for cid, slug in channels.items():
        aid = get_asset_id_static(cid, slug)
        if aid:
            # 匹配 workers.js 中的 key 字段并更新
            pattern = rf'"{cid}"\s*:\s*\{{[^}}]*?key\s*:\s*["\'][^"\']*["\']'
            replacement = f'"{cid}": {{ name: "", key: "{aid}" }}'
            
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                any_updated = True
        time.sleep(2)

    if any_updated:
        with open(workers_file, "w", encoding="utf-8") as f:
            f.write(content)
        print("🚀 [SUCCESS] 所有解析到的 ID 已同步至 workers.js")
    else:
        print("😭 静态解析也未捕获到数据。请确认您的 Mihomo 代理是否真正连上了台湾节点。")

if __name__ == "__main__":
    main()
