import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')

MAIN_STORY_CHARS = {
    '灰原哀', '赤井秀一', '安室透', '琴酒', '伏特加', '贝尔摩德', '宫野志保', '宫野明美',
    '朱蒂', '詹姆斯·布莱克', '安德烈·卡迈尔', '世良真纯', '冲矢昴', '本堂瑛海', '苏格兰',
    '朗姆', '黑田兵卫', '胁田兼则', '若狭留美', '玛丽', '领域外的妹妹', '羽田浩司',
    '枡山宪三', '沼渊己一郎', '宫野艾莲娜', '降谷零', '风见裕也', '库拉索', '爱尔兰',
    '香缇', '科伦', '黑衣组织'
}


def load_json(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        import json
        return json.load(f)


def is_main_story(episode):
    if episode.get('characters') is None:
        return False
    for c in episode['characters']:
        if c['name'] in MAIN_STORY_CHARS or c['category'] in ('组织成员', '黑衣组织'):
            return True
    return False


class APIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = dict(parse_qs(parsed.query))

        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        import json

        if path == '/api/bilibili':
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
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))

        elif path == '/api/original':
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
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))

        elif path == '/api/characters':
            bilibili_data = load_json('conan_episodes.json')
            chars = {}
            for ep in bilibili_data:
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
            self.wfile.write(json.dumps(char_list, ensure_ascii=False).encode('utf-8'))

        elif path == '/api/episode/bilibili':
            ep_num = query.get('ep', [''])[0]
            data = load_json('conan_episodes.json')
            for ep in data:
                if ep['bilibili_episode'] == ep_num:
                    self.wfile.write(json.dumps(ep, ensure_ascii=False).encode('utf-8'))
                    return
            self.wfile.write(json.dumps(None).encode('utf-8'))

        elif path == '/api/episode/original':
            ep_num = query.get('ep', [''])[0]
            data = load_json('conan_tv_original.json')
            for ep in data:
                if ep['tv_episode'] == ep_num:
                    self.wfile.write(json.dumps(ep, ensure_ascii=False).encode('utf-8'))
                    return
            self.wfile.write(json.dumps(None).encode('utf-8'))

        elif path == '/api/main_story':
            bilibili_data = load_json('conan_episodes.json')
            original_data = load_json('conan_tv_original.json')

            bilibili_main = []
            for ep in bilibili_data:
                if is_main_story(ep):
                    bilibili_main.append({
                        'episode': ep['bilibili_episode'],
                        'name': ep['name'],
                        'link': ep.get('link', ''),
                        'character_count': len(ep.get('characters') or []),
                        'characters': ep.get('characters') or []
                    })

            original_main = []
            for ep in original_data:
                if is_main_story(ep):
                    original_main.append({
                        'episode': ep['tv_episode'],
                        'tv_range': ep.get('tv_range', ep['tv_episode']),
                        'name': ep['name'],
                        'character_count': len(ep.get('characters') or []),
                        'characters': ep.get('characters') or []
                    })

            self.wfile.write(json.dumps({
                'bilibili': bilibili_main,
                'original': original_main
            }, ensure_ascii=False).encode('utf-8'))

        else:
            self.send_response(404)
            self.wfile.write(b'{"error":"not found"}')

    def log_message(self, format, *args):
        pass


if __name__ == '__main__':
    port = 3001
    server = HTTPServer(('0.0.0.0', port), APIHandler)
    print(f'API server running on port {port}')
    server.serve_forever()