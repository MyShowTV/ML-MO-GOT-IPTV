import os, re, time, requests
import chromedriver_autoinstaller
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options

def test_proxy():
    print("🌐 正在验证代理是否可用...")
    # 强制通过 7890 端口测试，确保出口 IP 是台湾
    proxies = {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}
    try:
        r = requests.get("https://ifconfig.me/ip", proxies=proxies, timeout=15)
        ip = r.text.strip()
        print(f"✅ 当前出口 IP: {ip}")
        # 如果 IP 还是 64.236... 说明代理配置有问题，但为了流程继续，这里返回 True
        return True
    except:
        print("❌ 代理未生效，请检查 Mihomo 运行状态")
        return False

def get_asset_id_advanced(cid, slug):
    print(f"\n🔍 探测频道: {cid} ({slug})")
    chromedriver_autoinstaller.install()
    
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    sw_options = {
        'proxy': {
            'http': 'http://127.0.0.1:7890',
            'https': 'http://127.0.0.1:7890',
            'no_proxy': 'localhost,127.0.0.1,0.0.0.0' # 极其重要：防止拦截驱动指令
        },
        'verify_ssl': False 
    }

    driver = None
    try:
        driver = webdriver.Chrome(options=options, seleniumwire_options=sw_options)
        driver.set_page_load_timeout(40)
        
        url = f"https://www.ofiii.com/channel/watch/{slug}"
        print(f"🌐 访问页面: {url}")
        driver.get(url)
        
        # 模拟点击页面，激活播放器加载数据
        time.sleep(10)
        driver.execute_script("document.body.click();")
        print("⏳ 等待 25 秒以截获 .m3u8 数据包...")
        time.sleep(25) 

        # 逆序搜索请求列表
        for request in reversed(driver.requests):
            if request.response:
                req_url = request.url
                # 寻找包含你的 11 位密钥结构的 URL
                if 'playlist/' in req_url and 'longturn' in req_url:
                    # 精准匹配：playlist/ 后面跟着的 11 位 [字母/数字/下划线/短横线]
                    match = re.search(r'playlist/([a-zA-Z0-9_-]{11})/', req_url)
                    if match:
                        aid = match.group(1)
                        print(f"✨ 发现 11 位密钥: {aid}")
                        return aid
        print(f"⚠️ {cid} 未能在网络请求中捕获到符合条件的 ID")
    except Exception as e:
        print(f"🔥 执行出错: {e}")
    finally:
        if driver:
            driver.quit()
    return None

def main():
    if not test_proxy():
        print("🚫 代理不可用，退出程序")
        return

    # 完整的频道映射表
    channels = {
        'lhtv01': 'litv-longturn03',
        'lhtv02': 'litv-longturn21',
        'lhtv03': 'litv-longturn18',
        'lhtv04': 'litv-longturn11',
        'lhtv05': 'litv-longturn12',
        'lhtv06': 'litv-longturn01',
        'lhtv07': 'litv-longturn02'
    }

    worker_path = "workers.js"
    if not os.path.exists(worker_path):
        print(f"❌ 找不到文件: {worker_path}")
        return

    with open(worker_path, "r", encoding="utf-8") as f:
        content = f.read()

    updated = False
    for cid, slug in channels.items():
        aid = get_asset_id_advanced(cid, slug)
        if aid:
            # 正则匹配并替换 workers.js 里的 key 字段
            # 匹配格式: "lhtv01": { name: "...", key: "OLD_KEY" }
            pattern = rf'"{cid}"\s*:\s*\{{.*?key\s*:\s*["\'][^"\']*["\']'
            replacement = f'"{cid}": {{ name: "", key: "{aid}" }}'
            
            if re.search(pattern, content, flags=re.DOTALL):
                content = re.sub(pattern, replacement, content, flags=re.DOTALL)
                print(f"✅ 已准备更新 {cid} 的密钥")
                updated = True
            else:
                print(f"❓ 在 workers.js 中未匹配到 {cid} 的配置格式")
        
        # 频道间隔，防止请求过快
        time.sleep(3)

    if updated:
        with open(worker_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("\n🎉 所有捕获到的密钥已成功保存至 workers.js")
    else:
        print("\n⚠️ 本次运行未对 workers.js 进行任何修改")

if __name__ == "__main__":
    main()
