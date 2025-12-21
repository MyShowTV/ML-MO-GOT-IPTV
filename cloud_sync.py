import os, re, time, base64
import chromedriver_autoinstaller
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options

def get_asset_id_advanced(cid, slug):
    print(f"🔍 探测频道: {cid} ({slug})")
    chromedriver_autoinstaller.install()
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--autoplay-policy=no-user-gesture-required")
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    # Bright Data 代理认证
    proxy_user = os.getenv("BD_USER")
    proxy_pass = os.getenv("BD_PASS")
    proxy_host = "brd.superproxy.io"
    proxy_port = "33335"

    if not proxy_user or not proxy_pass:
        print("⚠️ 缺少 Bright Data 账号或密码，请在 GitHub Secrets 中设置 BD_USER / BD_PASS")
        return None

    auth_header = "Basic " + base64.b64encode(f"{proxy_user}:{proxy_pass}".encode()).decode()
    sw_options = {
        'proxy': {
            'http': f"http://{proxy_host}:{proxy_port}",
            'https': f"https://{proxy_host}:{proxy_port}",
            'no_proxy': 'localhost,127.0.0.1'
        },
        'connection_timeout': None,
        'verify_ssl': False,
        'mitm_http2': False,
        'custom_authorization': auth_header
    }

    driver = None
    try:
        driver = webdriver.Chrome(options=options, seleniumwire_options=sw_options)
        driver.get(f"https://www.ofiii.com/channel/watch/{slug}")
        time.sleep(10)
        driver.execute_script("document.querySelector('body').click();")
        print(f"⏳ 正在监听数据流: {slug}")
        time.sleep(15)

        for request in reversed(driver.requests):
            url = request.url
            if '.m3u8' in url and ('playlist' in url or 'avc1' in url):
                match = re.search(r'playlist/([a-zA-Z0-9_-]+)/', url)
                if match:
                    aid = match.group(1)
                    print(f"✨ 发现密钥 {cid} → {aid}")
                    return aid
        print(f"❌ {cid} 未发现关键请求")
    except Exception as e:
        print(f"🔥 {cid} 错误: {e}")
    finally:
        if driver:
            driver.quit()
    return None


def main():
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
        print("✅ 所有频道密钥已更新完成 ✅")
    else:
        print("⚠️ 没有发现可更新的频道，请检查代理配置。")

if __name__ == "__main__":
    main()
