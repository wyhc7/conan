#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 conanpedia.com（柯南百科 MediaWiki）爬取每集登场角色数据。

流程：
1. 通过 allpages 分页获取所有 "TV*" 前缀的剧集页面标题
2. 批量获取 wikitext（每批 50 个标题）
3. 解析卡片中的「集数（拆分版xxx）」以及「登场角色」小节
4. 输出 cp_episodes.json（每页解析结果）与 cp_split_mapping.json（拆分版编号 -> 页面）

支持增量模式（仅抓取尚未抓取的页面，默认开启）。
"""
import json
import os
import re
import time
import urllib.request
import urllib.parse

API = "https://www.conanpedia.com/api.php"
HEADERS = {"User-Agent": "conan-episode-scraper/1.0 (GitHub Actions)"}

# 单一 JSON 缓存文件（wikitext 正文），便于 git 追踪与增量更新
WIKITEXT_CACHE = ".cache/wikitext.json"
EPISODES_OUT = ".cache/cp_episodes.json"
MAPPING_OUT = ".cache/cp_split_mapping.json"


# ------------------------- 通用工具 -------------------------

def strip_ref(text):
    return re.sub(r"<ref[^>]*>.*?</ref>", "", text, flags=re.S)


def display_text(raw):
    s = raw
    s = strip_ref(s)

    def repl_template(m):
        name = m.group(1).strip().split("|")[0]
        args = m.group(1).split("|")[1:]
        if name in ("jp", "ruby", "tt", "示亡号", "颜色", "color"):
            for a in args:
                a = a.strip()
                if a:
                    return a
            return ""
        return ""

    prev = None
    while prev != s:
        prev = s
        s = re.sub(r"\{\{([^{}]*)\}\}", repl_template, s)

    def repl_link(m):
        inner = m.group(1)
        if "|" in inner:
            return inner.split("|", 1)[1]
        return inner

    s = re.sub(r"\[\[([^\[\]]*)\]\]", repl_link, s)
    s = s.replace("&amp;", "&").replace("&nbsp;", " ").replace("&lt;", "<").replace("&gt;", ">")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def parse_wikitable(text):
    rows = []
    i = text.find("{|")
    if i < 0:
        return rows
    depth = 0
    start = i
    j = i
    block = None
    while True:
        n1 = text.find("{|", j + 2)
        n2 = text.find("|}", j + 2)
        if n2 < 0:
            break
        if n1 != -1 and n1 < n2:
            depth += 1
            j = n1
        else:
            if depth == 0:
                block = text[start:n2 + 2]
                break
            depth -= 1
            j = n2
    if block is None:
        block = text[start:]
    lines = block.split("\n")
    cur = None
    for ln in lines:
        ln = ln.rstrip()
        if ln.startswith("{|") or ln.startswith("|}") or ln.startswith("|-") or ln.startswith("!"):
            if cur is not None:
                rows.append(cur)
                cur = None
            continue
        if ln.startswith("|"):
            if cur is None:
                cur = []
            body = ln[1:]
            if body.startswith("+") or body.startswith("-"):
                continue
            if body.startswith("{|"):
                continue
            cur.append(body)
        elif ln.strip() == "":
            pass
        else:
            if cur is not None:
                cur[-1] = cur[-1] + " " + ln.strip()
    if cur is not None and len(cur) > 0:
        rows.append(cur)
    return rows


def _parse_header(text):
    cols = []
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("!") and "|" in line:
            after = line.split("|", 1)
            if len(after) > 1:
                cols.append(display_text(after[1]))
    return cols


def _safe_get(lst, idx):
    return lst[idx] if idx < len(lst) else ""


def parse_characters(wikitext):
    result = []
    m = re.search(r"==\s*登场角色\s*==", wikitext)
    if not m:
        return result
    body = wikitext[m.end():]
    endm = re.search(r"\n==([^=])", body)
    if endm:
        body = body[:endm.start()]
    sections = re.split(r"===\s*(常驻角色|案件角色|其他角色|黑影君)\s*===", body)
    if len(sections) > 1:
        for k in range(1, len(sections), 2):
            cat = sections[k]
            content = sections[k + 1]
            header_cols = _parse_header(content)
            has_jp = any("日文" in h for h in header_cols)
            rows = parse_wikitable(content)
            for row in rows:
                if not row:
                    continue
                cells = [display_text(c) for c in row]
                name = cells[0] if cells else ""
                if not name or "colspan" in name.lower():
                    continue
                entry = {"name": name, "category": cat}
                if cat == "常驻角色":
                    if has_jp:
                        entry["status"] = _safe_get(cells, 2)
                        entry["voice_actor"] = _safe_get(cells, 3)
                    else:
                        entry["status"] = _safe_get(cells, 1)
                        entry["voice_actor"] = _safe_get(cells, 2)
                elif cat == "案件角色":
                    entry["voice_actor"] = _safe_get(cells, 2 if has_jp else 1)
                elif cat == "其他角色":
                    entry["voice_actor"] = _safe_get(cells, 2 if has_jp else 1)
                elif cat == "黑影君":
                    entry["identity"] = _safe_get(cells, 1)
                result.append(entry)
    return result


def parse_card(wikitext):
    tv = None
    split = None
    cn = None
    m = re.search(r"\{\{卡片/内容\|集数\|([^}\n]+)\}\}", wikitext)
    if m:
        val = strip_ref(m.group(1)).strip()
        mm = re.match(r"^([\d\-]+)(?:\s*（拆分版([\d\-]+)）)?", val)
        if mm:
            tv = mm.group(1)
            split = mm.group(2)
    m2 = re.search(r"\{\{卡片/内容\|中文名[^|]*\|([^}\n]+)\}\}", wikitext)
    if m2:
        cn = display_text(m2.group(1))
    return tv, split, cn


def parse_episode(filename):
    w = open(filename, encoding="utf-8").read()
    tv, split, cn = parse_card(w)
    chars = parse_characters(w)
    return {"tv": tv, "split": split, "name": cn, "characters": chars}


# ------------------------- 网络请求 -------------------------

def api_get(params):
    q = urllib.parse.urlencode(params)
    req = urllib.request.Request(API + "?" + q, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def fetch_all_titles():
    titles = []
    cont = None
    while True:
        p = {
            "action": "query",
            "list": "allpages",
            "apprefix": "TV",
            "apnamespace": "0",
            "aplimit": "max",
            "apfilterredir": "nonredirects",
            "format": "json",
            "formatversion": "2",
        }
        if cont:
            p.update(cont)
        d = api_get(p)
        titles += [x["title"] for x in d["query"]["allpages"]]
        if "continue" not in d:
            break
        cont = d["continue"]
        time.sleep(0.2)
    return titles


def load_cache(cache_path=WIKITEXT_CACHE):
    """加载 wikitext 缓存（page_title -> wikitext 正文）"""
    if os.path.exists(cache_path):
        with open(cache_path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(cache, cache_path=WIKITEXT_CACHE):
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False)


def fetch_wikitext(titles, cache_path=WIKITEXT_CACHE):
    """批量获取 wikitext，只抓取缓存中不存在的页面"""
    cache = load_cache(cache_path)
    pending = [t for t in titles if t not in cache]
    if not pending:
        print("conanpedia: 无新增页面，全部命中缓存")
        return

    BATCH = 50
    for i in range(0, len(pending), BATCH):
        batch = pending[i:i + BATCH]
        try:
            d = api_get({
                "action": "query", "prop": "revisions", "rvprop": "content",
                "rvslots": "main", "redirects": "1",
                "titles": "|".join(batch), "format": "json", "formatversion": "2",
            })
        except Exception as e:
            print("conanpedia: 批次请求失败: %s" % e)
            time.sleep(3)
            continue
        for p in d.get("query", {}).get("pages", []):
            title = p.get("title", "")
            if "revisions" not in p:
                continue
            cache[title] = p["revisions"][0]["slots"]["main"]["content"]
        time.sleep(0.3)
    save_cache(cache, cache_path)
    print("conanpedia: 抓取完成，共新增 %d 个页面" % len(pending))


# ------------------------- 主流程 -------------------------

def build_outputs(cache_path=WIKITEXT_CACHE):
    cache = load_cache(cache_path)
    all_eps = {}
    for page_name, content in cache.items():
        tv, split, cn = parse_card(content)
        if not tv:
            continue
        chars = parse_characters(content)
        all_eps[page_name] = {
            "tv_range": tv, "split_range": split, "cn_name": cn, "characters": chars,
        }

    mapping = {}
    for pn, data in all_eps.items():
        sr = data["split_range"]
        if not sr:
            continue
        parts = sr.split("-")
        try:
            start = int(parts[0])
            end = int(parts[-1]) if len(parts) > 1 else start
            for n in range(start, end + 1):
                mapping[n] = pn
        except (ValueError, TypeError):
            pass

    os.makedirs(os.path.dirname(EPISODES_OUT), exist_ok=True)
    with open(EPISODES_OUT, "w", encoding="utf-8") as f:
        json.dump(all_eps, f, ensure_ascii=False, indent=1)
    with open(MAPPING_OUT, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=1)

    print("conanpedia: 解析 %d 个页面，映射 %d 个拆分版编号" % (len(all_eps), len(mapping)))
    return all_eps, mapping


def main():
    titles = fetch_all_titles()
    print("conanpedia: 共 %d 个 TV 页面" % len(titles))
    fetch_wikitext(titles)
    build_outputs()


if __name__ == "__main__":
    main()
