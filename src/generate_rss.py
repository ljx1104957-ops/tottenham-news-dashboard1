#!/usr/bin/env python3
"""
从 data/news.json 生成 RSS 2.0 feed.xml
"""

import json
from datetime import datetime, timezone
from pathlib import Path

try:
    from xml.sax.saxutils import escape
except ImportError:
    from xml.sax.saxutils import escape


def main():
    base = Path(__file__).parent.parent
    news_file = base / "data" / "news.json"
    out_file = base / "feed.xml"

    with open(news_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    items = data.get("items", [])
    updated = data.get("updated_at", datetime.now(timezone.utc).isoformat())

    rss_items = []
    for item in items[:50]:  # RSS 只放最近 50 条
        title = escape(item.get("title", ""))
        link = escape(item.get("link", ""))
        description = escape(item.get("summary", ""))
        pub_date = item.get("published", "")
        source = escape(item.get("source", ""))

        rss_items.append(f"""    <item>
      <title>{title}</title>
      <link>{link}</link>
      <guid isPermaLink="false">{escape(item.get("id", link))}</guid>
      <pubDate>{pub_date}</pubDate>
      <source>{source}</source>
      <description>{description}</description>
    </item>""")

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Spurs Daily · Tottenham Hotspur News</title>
    <link>https://your-username.github.io/tottenham-news-dashboard/</link>
    <description>托特纳姆热刺每日新闻聚合 — 中英文混合源，每天自动更新</description>
    <language>zh-CN</language>
    <lastBuildDate>{updated}</lastBuildDate>
{chr(10).join(rss_items)}
  </channel>
</rss>
"""

    with open(out_file, "w", encoding="utf-8") as f:
        f.write(xml)

    print(f"[OK] RSS 已生成 {out_file}，共 {len(items[:50])} 条")


if __name__ == "__main__":
    main()
