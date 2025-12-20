import os, re, time, requests
import chromedriver_autoinstaller
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options

def test_proxy():
    print("🌐 正在验证代理是否可用...")
    proxies = {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}
    try:
        ip = requests.get("https://ifconfig.me", proxies=proxies, timeout=10).text.strip()
        print(f"✅ 当前出口 IP: {ip}")
        return True
    except Exception as e:
        print(f"❌ 代理不可用: {e}")
        return False

def get_asset_id_advanced(cid, slug, retries=2):
    print(f"\n🔍 正在探测频道: {cid} ({slug}) ...")
    chromedriver_autoinstaller.install()

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--autoplay-policy=no-user-gesture-required")
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    sw_options = {
        'proxy': {
            'http': 'http://127.0.0.1:7890',
            'https': 'http://127.0.0.1:7890',
        }
    }

    for attempt in range(1, retries + 1):
        driver = None
        try:
            driver = webdriver.Chrome(options=options, seleniumwire_options=sw_options)
            url = f"https://www.ofiii.com/channel/watch/{slug}"
            print(f"🌐 第 {attempt} 次访问 {url}")
            driver.get(url)
            time.sleep(12)
            driver.execute_script("document.querySelector('body').click();")

            print("⏳ 等待视频数据加载中...")
            time.sleep(15)

            for request in reversed(driver.requests):
                if request.response and ".m3u8" in request.url:
                    url = request.url
                    if 'playlist' in url or 'avc1' in url:
                        match = re.search(r'playlist/([a-zA-Z0-9_-]+)/', url)
                        if match:
                            aid = match.group(1)
                            print(f"✨ 成功捕获密钥: {aid}")
                            return aid
            print(f"⚠️ 未捕获到有效数据包（第 {attempt} 次）")
        except Exception as e:
            print(f"🔥 {cid} 抓取出错（第 {attempt} 次）: {e}")
        finally:
            if driver: driver.quit()
        time.sleep(5)
    print(f"❌ {cid} 抓取失败（全部重试结束）")
    return None

def main():
    if not test_proxy():
        print("🚫 代理无效，终止运行。")
        return

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
    with open(worker_path, "r", encoding="utf-8") as f:
        content = f.read()

    updated = False
    for cid, slug in channels.items():
        aid = get_asset_id_advanced(cid, slug)
        if aid:
            pattern = rf'"{cid}"\s*:\s*\{{.*?key\s*:\s*["\'][^"\']*["\']'
            replacement = f'"{cid}": {{ name: "", key: "{aid}" }}'
            content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            updated = True
        time.sleep(2)

    if updated:
        with open(worker_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("✅ 所有频道密钥已更新至 workers.js")
    else:
        print("⚠️ 没有更新任何密钥")

if __name__ == "__main__":
    main()
