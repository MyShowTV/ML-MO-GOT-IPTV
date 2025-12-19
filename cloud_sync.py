name: 龙华频道 AssetID 自动同步

on:
  schedule:
    - cron: '0 0,12 * * *' # 每天两次
  workflow_dispatch:      # 允许手动执行

jobs:
  sync:
    runs-on: ubuntu-latest

    steps:
      - name: 检出代码
        uses: actions/checkout@v4

      - name: 初始化 Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: 安装基础依赖
        run: |
          pip install selenium webdriver-manager
          sudo apt-get update
          sudo apt-get install -y shadowsocks-libev

      - name: 开启 Shadowsocks 隧道
        run: |
          # 启动后台 shadowsocks-local
          ss-local -s 154.223.20.190 -p 8388 -k "${{ secrets.SS_PASSWORD }}" -m aes-256-gcm -l 10808 &
          
          echo "正在热身，等待代理隧道通畅..."
          for i in {1..10}; do
            # 使用 curl 探测 google 来确认代理是否真的通了
            if curl -x socks5://127.0.0.1:10808 -I https://www.google.com --connect-timeout 5; then
              echo "✅ 代理节点连接成功"
              exit 0
            fi
            echo "尝试建立连接中 ($i/10)..."
            sleep 5
          done
          echo "❌ 代理节点超时，请检查密码或 VPS 状态"
          exit 1

      - name: 运行同步脚本
        env:
          # 告诉 Python 脚本走 10808 代理
          HTTPS_PROXY: http://127.0.0.1:10808
          HTTP_PROXY: http://127.0.0.1:10808
          # 核心修正：禁止本地通信走代理，避免 RemoteDisconnected 报错
          NO_PROXY: localhost,127.0.0.1
        run: python longhua_sync.py

      - name: 自动提交更新
        run: |
          git config --local user.email "github-actions[bot]@users.noreply.github.com"
          git config --local user.name "github-actions[bot]"
          if [[ -n "$(git status --porcelain workers.js)" ]]; then
            git add workers.js
            git commit -m "🤖 自动同步 AssetID [$(date '+%Y-%m-%d %H:%M')]"
            git push
          else
            echo "数据未变动，无需推送"
          fi
