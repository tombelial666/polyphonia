#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Clean duplicate bookmarks from Chrome."""

import json
import hashlib
import sys
from pathlib import Path
from collections import defaultdict

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    bm_path = Path(r"C:\Users\Admin\AppData\Local\Google\Chrome\User Data\Default\Bookmarks")
    
    if not bm_path.exists():
        print(f"[ERROR] File not found: {bm_path}")
        return 1
    
    # Читаю файл
    with open(bm_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    def clean_bookmarks(node, seen_urls=None):
        """Рекурсивно удаляю дубли по URL."""
        if seen_urls is None:
            seen_urls = set()
        
        if 'children' not in node:
            return
        
        cleaned = []
        removed_count = 0
        
        for child in node.get('children', []):
            # Для папок — рекурсия
            if child.get('type') == 'folder':
                sub_removed = clean_bookmarks(child, seen_urls)
                removed_count += sub_removed
                cleaned.append(child)
            else:
                # Для URL — проверка дублей
                url = child.get('url', '')
                name = child.get('name', '')
                
                # Если URL уже встречался — пропускаю
                if url and url in seen_urls:
                    print(f"  [REMOVED] {name[:50]}")
                    removed_count += 1
                    continue
                
                if url:
                    seen_urls.add(url)
                
                cleaned.append(child)
        
        node['children'] = cleaned
        return removed_count
    
    total_removed = 0
    
    # Почищу roots
    for root_name in ['bookmark_bar', 'other', 'synced']:
        if root_name in data['roots']:
            print(f"Processing [{root_name}]...")
            removed = clean_bookmarks(data['roots'][root_name])
            total_removed += removed
    
    # Пересчитаю контрольную сумму
    json_str = json.dumps(data, separators=(',', ': '), ensure_ascii=False)
    checksum = hashlib.md5(json_str.encode('utf-8')).hexdigest()
    data['checksum'] = checksum
    
    # Сохраню
    with open(bm_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=3)
    
    print(f"\n[SUCCESS] Done!")
    print(f"   Removed duplicates: {total_removed}")
    print(f"   File saved with new checksum: {checksum}")
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
