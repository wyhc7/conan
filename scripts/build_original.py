#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 conanpedia 解析结果生成原版 TV 版数据 data/conan_tv_original.json。

与 data/conan_episodes.json（按 B站拆分版编号）不同，本文件按原版放送编号组织：
- 每个原版 TV 编号一条记录（合并页如 TV100-101 会展开为两条）
- 含拆分版编号范围、对应 B站编号、中文名、登场角色
- 一个原版集对应多个拆分版编号时（如 TV219 拆分版 235-238），bilibili_episodes 列出全部
"""
import json
import os

CP_EPISODES = ".cache/cp_episodes.json"
ORIGINAL_OUT = "data/conan_tv_original.json"


def expand_range(s):
    """将 '100-101' 或 '1' 展开为整数列表；无法解析返回空列表"""
    if not s:
        return []
    parts = str(s).split("-")
    try:
        start = int(parts[0])
        end = int(parts[-1]) if len(parts) > 1 else start
    except (ValueError, TypeError):
        return []
    return list(range(start, end + 1))


def build():
    if not os.path.exists(CP_EPISODES):
        raise RuntimeError("缺少 %s，请先运行 fetch_characters.py" % CP_EPISODES)

    cp_episodes = json.load(open(CP_EPISODES, encoding="utf-8"))

    output = []
    for page_name, data in cp_episodes.items():
        tvs = expand_range(data.get("tv_range"))
        splits = expand_range(data.get("split_range"))
        if not tvs:
            continue

        for idx, tv in enumerate(tvs):
            entry = {
                "tv_episode": str(tv),
                "tv_range": data.get("tv_range") or "",
                "split_range": data.get("split_range") or "",
                "bilibili_episodes": [],
                "name": data.get("cn_name") or "",
                "characters": data.get("characters") or [],
                "character_source": "https://www.conanpedia.com/" + page_name.replace(" ", "_"),
            }
            if splits:
                if len(splits) == len(tvs):
                    entry["bilibili_episodes"] = [splits[idx]]
                else:
                    entry["bilibili_episodes"] = splits
            output.append(entry)

    output.sort(key=lambda e: int(e["tv_episode"]))

    with open(ORIGINAL_OUT, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    filled = sum(1 for e in output if e.get("characters"))
    total = len(output)
    print("原版TV数据完成: %d 集，有角色数据 %d 集 (%.1f%%)" % (
        total, filled, filled / total * 100 if total else 0))

    covered = set(int(e["tv_episode"]) for e in output)
    missing = [n for n in range(1, max(covered) + 1) if n not in covered]
    if missing:
        ranges = []
        for n in missing:
            if not ranges or n > ranges[-1][1] + 1:
                ranges.append([n, n])
            else:
                ranges[-1][1] = n
        print("原版TV缺失的集数范围:")
        for r in ranges:
            print("  %s" % ("%d" % r[0] if r[0] == r[1] else "%d-%d" % (r[0], r[1])))


if __name__ == "__main__":
    build()
