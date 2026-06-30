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
  - optional TweetClaw JSON/JSONL export via --tweetclaw-export

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


def iter_objects(value):
    """Yield dictionaries from nested lists and dictionaries."""
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from iter_objects(child)
    elif isinstance(value, list):
        for item in value:
            yield from iter_objects(item)


def first_text(record, keys):
    """Return the first non-empty text value for any candidate key."""
    for key in keys:
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return ' '.join(value.split())
        if isinstance(value, (int, float)):
            return str(value)
    return ''


def first_metric(record, keys):
    """Return a metric from the record or nested metrics object."""
    sources = [record]
    metrics = record.get('metrics')
    if isinstance(metrics, dict):
        sources.append(metrics)
    metrics_parsed = record.get('metrics_parsed')
    if isinstance(metrics_parsed, dict):
        sources.append(metrics_parsed)

    for source in sources:
        for key in keys:
            value = source.get(key)
            if isinstance(value, (int, float)):
                return str(int(value))
            if isinstance(value, str) and value.strip():
                return value.strip()
    return '0'


def normalize_tweetclaw_post(record):
    """Normalize one TweetClaw-exported post into the dashboard post shape."""
    text = first_text(record, [
        'text',
        'full_text',
        'fullText',
        'tweetText',
        'tweet_text',
        'content',
        'body',
    ])
    if len(text) < 8:
        return None

    post_id = first_text(record, ['id', 'tweetId', 'tweet_id', 'postId', 'post_id'])
    url = first_text(record, ['url', 'tweetUrl', 'tweet_url', 'permalink', 'link'])
    timestamp = first_text(record, [
        'timestamp_iso',
        'timestamp',
        'createdAt',
        'created_at',
        'date',
    ])

    return {
        'id': post_id,
        'url': url,
        'text': text,
        'timestamp_iso': timestamp,
        'timestamp_display': timestamp[:10] if timestamp else '',
        'source': 'TweetClaw export',
        'metrics_parsed': {
            'replies': first_metric(record, ['replies', 'replyCount', 'reply_count']),
            'retweets': first_metric(record, [
                'retweets',
                'reposts',
                'retweetCount',
                'retweet_count',
            ]),
            'likes': first_metric(record, ['likes', 'likeCount', 'like_count', 'favorites']),
            'views': first_metric(record, ['views', 'viewCount', 'view_count', 'impressions']),
        },
        'comments': [],
    }


def load_tweetclaw_export(filepath):
    """Load TweetClaw JSON or JSONL and return normalized unique posts."""
    if not filepath:
        return []

    path = Path(filepath)
    raw = path.read_text(encoding='utf-8').strip()
    if not raw:
        return []

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = [json.loads(line) for line in raw.splitlines() if line.strip()]

    posts = []
    seen = set()
    for record in iter_objects(parsed):
        post = normalize_tweetclaw_post(record)
        if not post:
            continue
        key = post.get('id') or post.get('url') or post.get('text')
        if key in seen:
            continue
        seen.add(key)
        posts.append(post)
    return posts


def compile_data(username, data_dir, output_path, tweetclaw_export=None):
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

    # Merge optional TweetClaw export posts.
    tweetclaw_posts = load_tweetclaw_export(tweetclaw_export)
    for post in tweetclaw_posts:
        post_id = post.get('id') or post.get('url')
        if post_id and post_id not in existing_ids:
            posts_detail.append(post)
            existing_ids.add(post_id)

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

    data_sources = profile.get('data_sources', [
        "Browser scraping of X profile timeline",
        "Direct URL visits for individual posts",
        "Web search"
    ])
    if tweetclaw_posts:
        data_sources = [*data_sources, "TweetClaw export"]

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
            "data_sources": data_sources
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
    parser.add_argument('--tweetclaw-export')
    args = parser.parse_args()
    compile_data(args.username, args.data_dir, args.output, args.tweetclaw_export)
