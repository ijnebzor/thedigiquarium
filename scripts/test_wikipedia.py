#!/usr/bin/env python3
"""
Test Wikipedia access and link parsing for all languages
Run before starting tanks to ensure everything works
"""

import urllib.request
import urllib.parse
from html.parser import HTMLParser

# Configuration matching docker-compose
KIWIX_CONFIGS = {
    'english': {
        'url': 'http://localhost:8081',
        'base': '/wikipedia_en_simple_all_nopic_2026-02',
        'test_article': 'Science'
    },
    'spanish': {
        'url': 'http://localhost:8082',
        'base': '/wikipedia_es_all_nopic_2025-10',
        'test_article': 'Ciencia'
    },
    'german': {
        'url': 'http://localhost:8084',
        'base': '/wikipedia_de_all_nopic_2026-01',
        'test_article': 'Wissenschaft'
    },
    'chinese': {
        'url': 'http://localhost:8083',
        'base': '/wikipedia_zh_all_nopic_2025-09',
        'test_article': '科学'
    },
    'japanese': {
        'url': 'http://localhost:8085',
        'base': '/wikipedia_ja_all_nopic_2025-10',
        'test_article': '科学'
    }
}

EXCLUDE_PATTERNS = [
    '.css', '.js', '.png', '.jpg', '.svg', '.ico',
    'Special:', 'File:', 'Category:', 'Help:', 'Portal:', 'Template:', 'Wikipedia:', 'Talk:',
    'Especial:', 'Archivo:', 'Categoría:', 'Ayuda:', 'Plantilla:',
    'Spezial:', 'Datei:', 'Kategorie:', 'Hilfe:', 'Vorlage:',
    '特殊:', '文件:', '分类:', '帮助:',
    '特別:', 'ファイル:', 'カテゴリ:', 'ヘルプ:',
    '/mw/', '/w/', 'wikipedia', 'mediawiki', 'footer', 'header', 'sidebar', 'nav',
]


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            href = dict(attrs).get('href', '')
            if href and not href.startswith(('http://', 'https://', '//', '#', '_')):
                href_lower = href.lower()
                if not any(p.lower() in href_lower for p in EXCLUDE_PATTERNS):
                    self.links.append(href)


def test_language(lang, config):
    """Test Wikipedia access for a language"""
    print(f"\n{'='*50}")
    print(f"Testing: {lang.upper()}")
    print(f"{'='*50}")
    
    article = config['test_article']
    encoded = urllib.parse.quote(article, safe='')
    url = f"{config['url']}{config['base']}/{encoded}"
    
    print(f"URL: {url}")
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Test'})
        with urllib.request.urlopen(req, timeout=10) as r:
            html = r.read().decode('utf-8', errors='ignore')
        
        print(f"✅ Fetch successful: {len(html)} bytes")
        
        # Parse links
        parser = LinkParser()
        parser.feed(html)
        
        # Decode and filter links
        decoded_links = []
        seen = set()
        for link in parser.links:
            ln = link.lstrip('./')
            if ln.startswith('../') or len(ln) < 2:
                continue
            try:
                title = urllib.parse.unquote(ln).replace('_', ' ').split('/')[-1]
            except:
                continue
            if title not in seen and len(title) > 1:
                seen.add(title)
                decoded_links.append(title)
        
        print(f"✅ Links found: {len(decoded_links)}")
        
        if decoded_links:
            print(f"   Sample links:")
            for link in decoded_links[:5]:
                print(f"     - {link}")
            
            if len(decoded_links) >= 5:
                print(f"\n✅ {lang.upper()} PASSED - Ready for exploration")
                return True
            else:
                print(f"\n⚠️ {lang.upper()} WARNING - Only {len(decoded_links)} links found")
                return True
        else:
            print(f"\n❌ {lang.upper()} FAILED - No links parsed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    print("="*60)
    print("DIGIQUARIUM WIKIPEDIA PRE-FLIGHT TEST")
    print("="*60)
    
    results = {}
    for lang, config in KIWIX_CONFIGS.items():
        results[lang] = test_language(lang, config)
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    passed = sum(1 for r in results.values() if r)
    failed = sum(1 for r in results.values() if not r)
    
    for lang, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {lang}: {status}")
    
    print(f"\nTotal: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n✅ All languages ready for exploration!")
        return 0
    else:
        print(f"\n❌ {failed} language(s) have issues - fix before starting tanks")
        return 1


if __name__ == '__main__':
    exit(main())
