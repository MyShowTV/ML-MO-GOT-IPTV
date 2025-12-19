name: 自动同步 AssetID

on:
  schedule:
    - cron: '0 0,12 * * *'
  workflow_dispatch:

jobs:
  sync:
    runs-on: ubuntu-latest

    steps:
      - name: 检出代码
        uses: actions/checkout@v4

      - name: 设置 Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: 安装依赖
        run: |
          # 直接安装，不再寻找 requirements.txt
          pip install selenium webdriver-manager
          sudo apt-get update
          sudo apt-get install -y shadowsocks-libev

      - name: 启动 Shadowsocks 代理
        run: |
          # 请确认 SS_PASSWORD 已在 Secrets 中配置
          ss-local -s 154.223.20.190 -p 8388 -k "${{ secrets.SS_PASSWORD }}" -m aes-256-gcm -l 10808 &
          
          echo "等待代理启动..."
          for i in {1..10}; do
            if curl -x socks5://127.0.0.1:10808 -I https://www.google.com --connect-timeout 5; then
              echo "✅ 代理连接成功"
              exit 0
            fi
            sleep 3
          done
          echo "⚠️ 代理可能未连通，尝试继续运行脚本..."

      - name: 运行同步脚本
        env:
          HTTPS_PROXY: http://127.0.0.1:10808
          HTTP_PROXY: http://127.0.0.1:10808
          NO_PROXY: localhost,127.0.0.1
        run: python cloud_sync.py

      - name: 提交更新
        run: |
          git config --local user.email "github-actions[bot]@users.noreply.github.com"
          git config --local user.name "github-actions[bot]"
          if [[ -n "$(git status --porcelain workers.js)" ]]; then
            git add workers.js
            git commit -m "🤖 自动更新 AssetID"
            git push
          else
            echo "无变动"
          fi
