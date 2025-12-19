import os, re

def sync():
    # --- 在这里直接填入你用 F12 看到的最新 ID ---
    # 根据你之前提供的信息，我填入了你抓到的几个 ID
    manual_data = {
        'lhtv01': '-1lPJzJEZYc', # 龙华电影
        'lhtv03': 'LQdetS7vEBE', # 龙华戏剧
        'lhtv05': 'B8KQyHS-600', # 龙华偶像
        'lhtv06': 'ZlRqsFWifLk', # 龙华卡通
        'lhtv07': 'ofiii76_id_here' # 请填入你抓到的 lhtv07 的 ID
    }
    
    file_path = "workers.js"
    if not os.path.exists(file_path):
        print("❌ 错误: 找不到 workers.js")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    any_updated = False
    for cid, aid in manual_data.items():
        # 精准匹配 "cid": { ... key: "..." }
        pattern = rf'"{cid}"\s*:\s*\{{[^}}]+?key\s*:\s*["\'][^"\']*["\']'
        replacement = f'"{cid}": {{ name: "", key: "{aid}" }}'
        
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            print(f"✅ {cid} 已准备更新为: {aid}")
            any_updated = True
        else:
            print(f"⚠️ {cid} 在 workers.js 中匹配失败，请检查格式")

    if any_updated:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("🚀 手动同步数据已写入 workers.js！请提交并等待部署。")
    else:
        print("😭 未能更新任何数据。")

if __name__ == "__main__":
    sync()
