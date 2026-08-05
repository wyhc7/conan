#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 B站 PGC API 获取《名侦探柯南》剧集基础数据（集数、名称、链接、发布时间）。
保存到 data/conan_bilibili_base.json
"""
import json
import datetime
import time
import urllib.request

SEASON_ID = "33378"  # B站《名侦探柯南》season_id
API_URL = "https://api.bilibili.com/pgc/view/web/season?season_id=%s" % SEASON_ID
OUTPUT = "data/conan_bilibili_base.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Referer": "https://www.bilibili.com/bangumi/play/ss%s" % SEASON_ID,
}


def fetch():
    req = urllib.request.Request(API_URL, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.load(r)


def main():
    data = fetch()
    if data.get("code") != 0:
        raise RuntimeError("B站 API 返回错误: %s" % json.dumps(data, ensure_ascii=False)[:300])

    episodes = data["result"]["episodes"]
    base = []
    for e in episodes:
        ts = e.get("pub_time")
        pub = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d") if ts else None
        base.append({
            "bilibili_episode": e["title"],
            "name": e["long_title"],
            "link": e["link"],
            "ep_id": e["ep_id"],
            "bvid": e.get("bvid"),
            "pub_date": pub,
            "duration": e.get("duration"),
            "characters": None,
            "character_source": None,
        })

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(base, f, ensure_ascii=False, indent=1)

    print("B站数据更新完成: %d 集 -> %s" % (len(base), OUTPUT))
    # 输出最新一集便于核对
    if base:
        latest = base[-1]
        print("最新一集: %s | %s | %s" % (latest["bilibili_episode"], latest["name"], latest["pub_date"]))


if __name__ == "__main__":
    main()
