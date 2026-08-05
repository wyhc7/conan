import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(ROOT, 'data')
OUT_DIR = os.path.join(ROOT, 'conan-tracker', 'public', 'data')

MAIN_STORY_CHARS = {
    '琴酒', '伏特加', '贝尔摩德', '朗姆', '黑田兵卫', '胁田兼则', '若狭留美',
    '赤井秀一', '安室透', '降谷零', '冲矢昴', '世良真纯', '玛丽', '领域外的妹妹',
    '朱蒂', '詹姆斯·布莱克', '安德烈·卡迈尔', '本堂瑛海', '宫野志保', '苏格兰',
    '库拉索', '爱尔兰', '香缇', '科伦', '枡山宪三', '风见裕也', '沼渊己一郎',
    '羽田浩司'
}


def load_json(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def is_main_story(episode):
    if episode.get('characters') is None:
        return False
    for c in episode['characters']:
        if c['name'] in MAIN_STORY_CHARS:
            return True
    return False


def build_bilibili():
    data = load_json('conan_episodes.json')
    result = []
    for ep in data:
        result.append({
            'episode': ep['bilibili_episode'],
            'name': ep['name'],
            'link': ep.get('link', ''),
            'pub_date': ep.get('pub_date', ''),
            'character_count': len(ep.get('characters') or []),
            'is_main_story': is_main_story(ep),
            'characters': ep.get('characters') or []
        })
    return result


def build_original():
    data = load_json('conan_tv_original.json')
    result = []
    for ep in data:
        result.append({
            'episode': ep['tv_episode'],
            'tv_range': ep.get('tv_range', ep['tv_episode']),
            'bilibili_episodes': ep.get('bilibili_episodes', []),
            'name': ep['name'],
            'character_count': len(ep.get('characters') or []),
            'is_main_story': is_main_story(ep),
            'characters': ep.get('characters') or []
        })
    return result


def build_characters():
    data = load_json('conan_episodes.json')
    chars = {}
    for ep in data:
        if ep.get('characters') is None:
            continue
        for c in ep['characters']:
            name = c['name']
            if name not in chars:
                chars[name] = []
            chars[name].append(ep['bilibili_episode'])
    char_list = []
    for name, eps in chars.items():
        char_list.append({
            'name': name,
            'episode_count': len(eps),
            'episodes': sorted([int(e) for e in eps])
        })
    char_list.sort(key=lambda x: -x['episode_count'])
    return char_list


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    bilibili = build_bilibili()
    original = build_original()
    characters = build_characters()

    with open(os.path.join(OUT_DIR, 'bilibili.json'), 'w', encoding='utf-8') as f:
        json.dump(bilibili, f, ensure_ascii=False)
    with open(os.path.join(OUT_DIR, 'original.json'), 'w', encoding='utf-8') as f:
        json.dump(original, f, ensure_ascii=False)
    with open(os.path.join(OUT_DIR, 'characters.json'), 'w', encoding='utf-8') as f:
        json.dump(characters, f, ensure_ascii=False)

    print(f'bilibili: {len(bilibili)} episodes')
    print(f'original: {len(original)} episodes')
    print(f'characters: {len(characters)}')
    print(f'output -> {OUT_DIR}')


if __name__ == '__main__':
    main()