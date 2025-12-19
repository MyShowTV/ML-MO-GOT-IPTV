export default {
  async fetch(request) {
    const url = new URL(request.url);
    // 获取路径并转为小写，例如访问 /lhtv01 得到 "lhtv01"
    const path = url.pathname.replace(/^\/|\.m3u8$/gi, "").toLowerCase();

    // 频道配置表
    // 注意：Python 脚本会自动替换 key: "..." 里的内容，请不要修改这里的结构
    const config = {
      "lhtv01": { name: "龙华电影", key: "这里填钥匙" },
      "lhtv02": { name: "龙华经典", key: "这里填钥匙" },
      "lhtv03": { name: "龙华戏剧", key: "这里填钥匙" },
      "lhtv04": { name: "龙华日韩", key: "这里填钥匙" },
      "lhtv05": { name: "龙华偶像", key: "这里填钥匙" },
      "lhtv06": { name: "龙华卡通", key: "这里填钥匙" },
      "lhtv07": { name: "龙华洋片", key: "这里填钥匙" }
    };

    const ch = config[path];

    // 如果找不到频道或钥匙还没同步
    if (!ch || ch.key === "这里填钥匙") {
      return new Response(`频道 ${path} 尚未同步或不存在，请等待 GitHub Actions 运行。`, { 
        status: 404,
        headers: { "Content-Type": "text/plain;charset=utf-8" } 
      });
    }

    // 构造 Ofiii 的原始 m3u8 地址
    const m3u8Url = `https://cdi.ofiii.com/ocean/video/playlist/${ch.key}/master.m3u8`;

    try {
      // 代理请求 Ofiii，必须带上 Referer 否则会 403
      const response = await fetch(m3u8Url, {
        headers: {
          "Referer": "https://www.ofiii.com/",
          "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
      });

      const text = await response.text();

      // 修正 m3u8 内部的相对路径，确保在不同播放器中都能播放
      const baseUrl = m3u8Url.substring(0, m3u8Url.lastIndexOf('/') + 1);
      const fixedText = text.split('\n').map(line => {
        if (line.trim() && !line.startsWith('#') && !line.startsWith('http')) {
          return baseUrl + line;
        }
        return line;
      }).join('\n');

      return new Response(fixedText, {
        headers: {
          "Content-Type": "application/vnd.apple.mpegurl",
          "Access-Control-Allow-Origin": "*", // 允许跨域播放
          "Cache-Control": "public, max-age=3600"
        }
      });

    } catch (e) {
      return new Response("Error: " + e.message, { status: 500 });
    }
  }
};
