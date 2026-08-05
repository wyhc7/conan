#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合并 B站基础数据 + conanpedia 角色数据，更新最终 data/conan_episodes.json。

流程：
1. 读取 data/conan_bilibili_base.json（B站剧集列表）
2. 读取 .cache/cp_episodes.json + .cache/cp_split_mapping.json（conanpedia 角色数据）
3. 按拆分版编号映射，合并生成 data/conan_episodes.json
4. 输出覆盖统计（用于 GitHub Actions 判断是否有更新）
"""
import json
import os

BASE_OUT = "data/conan_bilibili_base.json"
EPISODES_OUT = "data/conan_episodes.json"
CP_EPISODES = ".cache/cp_episodes.json"
CP_MAPPING = ".cache/cp_split_mapping.json"


def main():
    if not os.path.exists(BASE_OUT):
        raise RuntimeError("缺少 %s，请先运行 fetch_bilibili.py" % BASE_OUT)
    if not os.path.exists(CP_EPISODES) or not os.path.exists(CP_MAPPING):
        raise RuntimeError("缺少 conanpedia 缓存，请先运行 fetch_characters.py")

    base = json.load(open(BASE_OUT, encoding="utf-8"))
    cp_episodes = json.load(open(CP_EPISODES, encoding="utf-8"))
    cp_mapping = json.load(open(CP_MAPPING, encoding="utf-8"))
    mapping_int = {int(k): v for k, v in cp_mapping.items()}

    filled_before = sum(1 for e in base if e.get("characters"))

    output = []
    for ep in base:
        entry = {
            "bilibili_episode": ep["bilibili_episode"],
            "name": ep["name"],
            "link": ep["link"],
            "pub_date": ep["pub_date"],
        }
        chars = None
        source = None
        t = ep["bilibili_episode"]
        if t.isdigit():
            n = int(t)
            if n in mapping_int:
                pn = mapping_int[n]
                if pn in cp_episodes:
                    chars = [
                        {
                            "name": c["name"],
                            "category": c.get("category"),
                            "status": c.get("status"),
                            "voice_actor": c.get("voice_actor"),
                        }
                        for c in cp_episodes[pn]["characters"]
                    ]
                    source = "https://www.conanpedia.com/" + pn.replace(" ", "_")
        if chars:
            entry["characters"] = chars
            entry["character_source"] = source
        else:
            entry["characters"] = None
        output.append(entry)

    with open(EPISODES_OUT, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    filled_after = sum(1 for e in output if e.get("characters"))
    total = len(output)
    print("合并完成: %d 集，有角色数据 %d 集 (%.1f%%)" % (
        total, filled_after, filled_after / total * 100 if total else 0))
    print("本次新增角色数据: %d 集" % (filled_after - filled_before))

    # 统计缺失范围，便于人工追踪
    missing = [int(e["bilibili_episode"]) for e in output
               if e["characters"] is None and e["bilibili_episode"].isdigit()]
    if missing:
        missing.sort()
        ranges = []
        for n in missing:
            if not ranges or n > ranges[-1][1] + 1:
                ranges.append([n, n])
            else:
                ranges[-1][1] = n
        print("仍缺失的集数范围:")
        for r in ranges:
            print("  %s" % ("%d" % r[0] if r[0] == r[1] else "%d-%d" % (r[0], r[1])))

    return filled_after - filled_before


if __name__ == "__main__":
    main()
