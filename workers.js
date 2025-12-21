export default {
  async fetch(request) {
    const url = new URL(request.url);
    const path = url.pathname.replace(/^\/|\.m3u8$/gi, "").toLowerCase();

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
    if (!ch || ch.key === "这里填钥匙") {
      return new Response("频道未就绪或未找到", { status: 404 });
    }

    const m3u8Url = `https://cdi.ofiii.com/ocean/video/playlist/${ch.key}/master.m3u8`;
    const res = await fetch(m3u8Url, {
      headers: {
        "Referer": "https://www.ofiii.com/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
      }
    });
    let text = await res.text();
    const baseUrl = m3u8Url.substring(0, m3u8Url.lastIndexOf('/') + 1);
    const fixed = text.split('\n').map(line => {
      if (line.trim() && !line.startsWith('#') && !line.startsWith('http')) return baseUrl + line;
      return line;
    }).join('\n');
    return new Response(fixed, {
      headers: {
        "Content-Type": "application/vnd.apple.mpegurl",
        "Access-Control-Allow-Origin": "*",
        "Cache-Control": "no-cache"
      }
    });
  }
};
