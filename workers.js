export default {
  async fetch(request) {
    const url = new URL(request.url);
    const path = url.pathname.replace(/^\/|\.m3u8$/gi, "").toLowerCase();

    // 频道列表 (Python 脚本会自动替换这里的 key 内容)
    const config = {
      "lhtv01": { name: "龙华电影", key: "LQdetS7vEBE" },
      "lhtv02": { name: "龙华经典", key: "LQdetS7vEBE" },
      "lhtv03": { name: "龙华戏剧", key: "LQdetS7vEBE" },
      "lhtv04": { name: "龙华日韩", key: "LQdetS7vEBE" },
      "lhtv05": { name: "龙华偶像", key: "4pYg_LvlA_Y" },
      "lhtv06": { name: "龙华卡通", key: "LQdetS7vEBE" },
      "lhtv07": { name: "龙华洋片", key: "LQdetS7vEBE" }
    };

    const ch = config[path];
    if (!ch) return new Response("Channel Not Found", { status: 404 });

    const m3u8Url = `https://cdi.ofiii.com/ocean/video/playlist/${ch.key}/master.m3u8`;

    try {
      const response = await fetch(m3u8Url, {
        headers: {
          "Referer": "https://www.ofiii.com/",
          "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
      });

      const text = await response.text();
      const baseUrl = m3u8Url.substring(0, m3u8Url.lastIndexOf('/') + 1);
      
      const fixedText = text.split('\n').map(line => {
        if (line.trim() && !line.startsWith('#') && !line.startsWith('http')) {
          return baseUrl + line;
        }
        return line;
      }).join('\n');

      return new Response(fixedText, {
        headers: { "Content-Type": "application/vnd.apple.mpegurl", "Access-Control-Allow-Origin": "*" }
      });
    } catch (e) {
      return new Response("Error: " + e.message, { status: 500 });
    }
  }
};
