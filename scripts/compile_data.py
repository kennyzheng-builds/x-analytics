#!/usr/bin/env python3
"""
Compile scraped X/Twitter data from multiple sources into a unified JSON file.

Usage:
    python3 compile_data.py --username USERNAME --data-dir /tmp/x_scrape --output output.json

Input: Reads JSON files from --data-dir:
  - profile.json        (profile metadata)
  - timeline_posts.json  (posts from timeline scrolling)
  - posts_detail/*.json  (individual post details)
  - comments/*.json      (comment data per post)
  - web_search.json      (posts found via web search)

Output: Unified JSON with structure:
  { meta, posts_detail[], timeline_all_posts[] }
"""

import json
import os
import sys
import argparse
from pathlib import Path


def parse_metric(val):
    """Parse metric strings like '1.2K', '3.1M' into numbers."""
    if not val:
        return 0
    val = str(val).strip().replace(',', '')
    multipliers = {'K': 1000, 'k': 1000, 'M': 1000000, 'm': 1000000}
    for suffix, mult in multipliers.items():
        if val.endswith(suffix):
            try:
                return int(float(val[:-1]) * mult)
            except ValueError:
                return 0
    try:
        return int(float(val))
    except ValueError:
        return 0


def load_json(filepath):
    """Safely load a JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError, UnicodeDecodeError):
        return None


def compile_data(username, data_dir, output_path):
    data_dir = Path(data_dir)

    # Load profile
    profile = load_json(data_dir / 'profile.json') or {}

    # Load timeline posts
    timeline = load_json(data_dir / 'timeline_posts.json') or []

    # Load detailed posts
    posts_detail = []
    detail_dir = data_dir / 'posts_detail'
    if detail_dir.exists():
        for f in sorted(detail_dir.glob('*.json')):
            post = load_json(f)
            if post:
                posts_detail.append(post)

    # Load comments
    comments_dir = data_dir / 'comments'
    comments_map = {}
    if comments_dir.exists():
        for f in comments_dir.glob('*.json'):
            cdata = load_json(f)
            if cdata:
                post_id = f.stem
                comments_map[post_id] = cdata

    # Attach comments to detailed posts
    for post in posts_detail:
        pid = post.get('id', '')
        if pid in comments_map:
            post['comments'] = comments_map[pid]

    # Load web search supplementary data
    web_data = load_json(data_dir / 'web_search.json') or []

    # Merge web search posts into detail if not already present
    existing_ids = {p.get('id') for p in posts_detail}
    for wp in web_data:
        if wp.get('id') and wp['id'] not in existing_ids:
            posts_detail.append(wp)
            existing_ids.add(wp['id'])

    # Sort by timestamp
    def sort_key(p):
        ts = p.get('timestamp_iso') or p.get('timestamp') or ''
        return ts
    posts_detail.sort(key=sort_key, reverse=True)

    # Deduplicate timeline
    seen = set()
    unique_timeline = []
    for t in timeline:
        tid = t.get('id') or t.get('url', '')
        if tid not in seen:
            seen.add(tid)
            unique_timeline.append(t)

    # Build output
    result = {
        "meta": {
            "user": username,
            "display_name": profile.get('display_name', username),
            "bio": profile.get('bio', ''),
            "location": profile.get('location', ''),
            "website": profile.get('website', ''),
            "followers": profile.get('followers', 0),
            "following": profile.get('following', 0),
            "total_posts": profile.get('total_posts', len(posts_detail)),
            "scraped_at": profile.get('scraped_at', ''),
            "data_sources": profile.get('data_sources', [
                "Browser scraping of X profile timeline",
                "Direct URL visits for individual posts",
                "Web search"
            ])
        },
        "posts_detail": posts_detail,
        "timeline_all_posts": unique_timeline
    }

    # Write output
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Compiled {len(posts_detail)} detailed posts + {len(unique_timeline)} timeline posts")
    print(f"Output: {output_path} ({output_path.stat().st_size / 1024:.1f} KB)")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Compile X/Twitter scraped data')
    parser.add_argument('--username', required=True)
    parser.add_argument('--data-dir', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    compile_data(args.username, args.data_dir, args.output)
