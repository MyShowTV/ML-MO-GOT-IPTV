export default {
  async fetch(request) {
    const url = new URL(request.url);
    // 获取路径并转为小写，例如访问 /lhtv01 得到 "lhtv01"
    const path = url.pathname.replace(/^\/|\.m3u8$/gi, "").toLowerCase();

    // 频道配置表
    // 注意：Python 脚本会自动替换 key: "..." 里的内容，请不要修改这里的结构
    const config = {
  "lhtv01": { name: "", key: "-1lPJzJEZYc" },
  "lhtv02": { name: "龙华经典", key: "这里填钥匙" },
  "lhtv03": { name: "", key: "LQdetS7vEBE" },
  "lhtv04": { name: "龙华日韩", key: "这里填钥匙" },
  "lhtv05": { name: "", key: "B8KQyHS-600" },
  "lhtv06": { name: "", key: "ZlRqsFWifLk" },
  "lhtv07": { name: "", key: "ofiii76_id_here" }
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

6.cloudflare

let channelKeys = {};

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const host = url.host;
    const path = url.pathname.replace(/^\/|\.m3u8$/gi, "").toLowerCase();
    const UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36";

    // 1. 钥匙接收端
    if (path === "update_key" && request.method === "POST") {
      const data = await request.json();
      if (data.pw !== "your_password_666") return new Response("Forbidden", {status: 403});
      channelKeys[data.id] = data.key;
      return new Response("OK");
    }

    // 2. 完整频道表
    const config = {
      // 成都系列 (实时解析)
      "cdtv1": { name: "成都新闻", api: "https://www.cditv.cn/live/getLiveUrl?url=https%3A%2F%2Fcdn1.cditv.cn%2Fcdtv1high%2FCDTV1High.flv%2Fplaylist.m3u8", type: "cdtv" },
      "cdtv2": { name: "成都经济", api: "https://www.cditv.cn/live/getLiveUrl?url=https%3A%2F%2Fcdn1.cditv.cn%2Fcdtv2high%2FCDTV2High.flv%2Fplaylist.m3u8", type: "cdtv" },
      "cdtv3": { name: "成都都市", api: "https://www.cditv.cn/live/getLiveUrl?url=https%3A%2F%2Fcdn1.cditv.cn%2Fcdtv3high%2FCDTV3High.flv%2Fplaylist.m3u8", type: "cdtv" },
      "cdtv4": { name: "成都影视", api: "https://www.cditv.cn/live/getLiveUrl?url=https%3A%2F%2Fcdn1.cditv.cn%2Fcdtv4high%2FCDTV4High.flv%2Fplaylist.m3u8", type: "cdtv" },
      "cdtv5": { name: "成都公共", api: "https://www.cditv.cn/live/getLiveUrl?url=https%3A%2F%2Fcdn1.cditv.cn%2Fcdtv5high%2FCDTV5High.flv%2Fplaylist.m3u8", type: "cdtv" },
      "cdtv6": { name: "成都少儿", api: "https://www.cditv.cn/live/getLiveUrl?url=https%3A%2F%2Fcdn1.cditv.cn%2Fcdtv6high%2FCDTV6High.flv%2Fplaylist.m3u8", type: "cdtv" },

      // 四川系列 (实时解析)
      "sctv1": { name: "四川卫视", api: "https://api.sctv.com/api/live/get_live_url?id=1", type: "sctv" },
      "sctv2": { name: "四川新闻", api: "https://api.sctv.com/api/live/get_live_url?id=2", type: "sctv" },
      "sctv3": { name: "四川经济", api: "https://api.sctv.com/api/live/get_live_url?id=3", type: "sctv" },
      "sctv4": { name: "四川文旅", api: "https://api.sctv.com/api/live/get_live_url?id=4", type: "sctv" },
      "sctv5": { name: "四川影视", api: "https://api.sctv.com/api/live/get_live_url?id=5", type: "sctv" },
      "sctv7": { name: "四川妇儿", api: "https://api.sctv.com/api/live/get_live_url?id=7", type: "sctv" },
      "sctv9": { name: "四川公共", api: "https://api.sctv.com/api/live/get_live_url?id=9", type: "sctv" },

      // 龙华系列 (推送模式)
      "lhtv01": { name: "龙华电影", id: "litv-longturn03", type: "gh" },
      "lhtv02": { name: "龙华经典", id: "litv-longturn21", type: "gh" },
      "lhtv03": { name: "龙华戏剧", id: "litv-longturn18", type: "gh" },
      "lhtv04": { name: "龙华日韩", id: "litv-longturn11", type: "gh" },
      "lhtv05": { name: "龙华偶像", id: "litv-longturn12", type: "gh" },
      "lhtv06": { name: "龙华卡通", id: "litv-longturn01", type: "gh" },
      "lhtv07": { name: "龙华洋片", id: "litv-longturn02", type: "gh" }
    };

    if (path === "" || path === "index") return renderIndex(host, config, channelKeys);
    const ch = config[path];
    if (!ch) return new Response("Not Found", { status: 404 });

    try {
      if (ch.type === "gh") {
        const assetId = channelKeys[ch.id];
        if (!assetId) return new Response("钥匙未同步", { status: 503 });
        return proxyM3u8(`https://cdi.ofiii.com/ocean/video/playlist/${assetId}/master.m3u8`, "https://www.ofiii.com/", UA);
      }
      if (ch.type === "cdtv") {
        const r = await fetch(ch.api, { headers: { "Referer": "https://www.cditv.cn/", "User-Agent": UA } });
        const text = await r.text();
        const match = text.replace(/\\/g, "").match(/https?:\/\/[^\s"'<>|]+?\.m3u8\?[^\s"'<>|]+/);
        return match ? Response.redirect(match[0], 302) : new Response("CDTV Match Error", {status: 500});
      }
      if (ch.type === "sctv") {
        const r = await fetch(ch.api, { headers: { "Referer": "https://www.sctv.com/", "User-Agent": UA } });
        const json = await r.json();
        const finalUrl = json.data?.url || json.url;
        return finalUrl ? Response.redirect(finalUrl, 302) : new Response("SCTV JSON Error", {status: 500});
      }
    } catch (e) {
      return new Response("Error: " + e.message, { status: 500 });
    }
  }
};

async function proxyM3u8(url, referer, ua) {
  const res = await fetch(url, { headers: { "Referer": referer, "User-Agent": ua } });
  let content = await res.text();
  const baseUrl = url.substring(0, url.lastIndexOf('/') + 1);
  const fixed = content.split('\n').map(line => {
    if (line.trim() && !line.startsWith('#') && !line.startsWith('http')) return baseUrl + line;
    return line;
  }).join('\n');
  return new Response(fixed, { headers: { "Content-Type": "application/vnd.apple.mpegurl", "Access-Control-Allow-Origin": "*" } });
}

function renderIndex(host, config, keys) {
  let html = `<html><head><meta charset="utf-8"><title>IPTV</title></head><body><h1>📡 20 合 1 直播源</h1><ul>`;
  for (const id in config) {
    const ch = config[id];
    const status = ch.type === 'gh' ? (keys[ch.id] ? "✅ 已同步" : "❌ 未同步") : "⚡ 实时抓取";
    html += `<li><b>${ch.name}</b>: <code>https://${host}/${id}.m3u8</code> [${status}]</li>`;
  }
  html += `</ul></body></html>`;
  return new Response(html, { headers: { "Content-Type": "text/html;charset=UTF-8" } });
}
