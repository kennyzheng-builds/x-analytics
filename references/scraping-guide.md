# X/Twitter Scraping Guide

## Data Source Priority

Use multiple sources to maximize coverage. X's algorithmic timeline does NOT show posts chronologically.

### Source 1: Browser Profile Scraping

Navigate to profile and extract visible tweets by injecting `scripts/extract_tweets.js`.

```
browser navigate "https://x.com/USERNAME"
```

Wait for page load, then extract profile metadata:
```js
JSON.stringify({
  display_name: document.querySelector('[data-testid="UserName"]')?.innerText.split('\n')[0] || '',
  bio: document.querySelector('[data-testid="UserDescription"]')?.innerText || '',
  followers: document.querySelector('a[href$="/verified_followers"]')?.innerText || '',
  following: document.querySelector('a[href$="/following"]')?.innerText || ''
})
```

Scroll-and-extract loop (collect 80-120 posts):
```bash
for i in $(seq 1 20); do
  browser console exec "window.scrollBy(0, 3000)"
  sleep 2
  TWEETS=$(browser console exec "$(cat scripts/extract_tweets.js)")
  # Append new tweets to collection
done
```

Save as `/tmp/x_scrape/timeline_posts.json`.

### Source 2: Web Search

Search for posts not visible in algorithmic timeline:
```
"USERNAME" site:x.com 2026
"@USERNAME" latest post
USERNAME twitter recent
```

This finds viral posts and recent content that the algorithm may not surface on the profile page.

### Source 3: TikHub API (Optional)

If user provides a TikHub API key:

**Get user posts:**
```bash
curl -X GET "https://api.tikhub.io/api/v1/twitter/web/fetch_user_post_tweet?screen_name=USERNAME&count=40" \
  -H "Authorization: Bearer API_KEY"
```

**Get post detail:**
```bash
curl -X GET "https://api.tikhub.io/api/v1/twitter/web/fetch_tweet_detail?tweet_id=TWEET_ID" \
  -H "Authorization: Bearer API_KEY"
```

**Get comments:**
```bash
curl -X GET "https://api.tikhub.io/api/v1/twitter/web/fetch_post_comments?tweet_id=TWEET_ID" \
  -H "Authorization: Bearer API_KEY"
```

Handle 402 (insufficient balance) gracefully -- fall back to browser scraping.

### Source 4: Direct Post Visits

For each discovered post URL, visit directly to get full content and metrics:
```
browser navigate "https://x.com/USERNAME/status/POST_ID"
```

Extract with JS:
```js
const article = document.querySelector('article[data-testid="tweet"]');
const text = article?.querySelector('[data-testid="tweetText"]')?.innerText || '';
const time = article?.querySelector('time')?.getAttribute('datetime') || '';
const stats = article?.querySelector('[role="group"]')?.innerText || '';
```

### Source 5: Comment/Audience Collection

X blocks comment viewing without login. Alternative sources:

- **Substack**: `site:substack.com "USERNAME"` -- check comments sections
- **GitHub**: `gh api repos/USERNAME/REPO/issues` -- check issues and PR discussions
- **Reddit**: `site:reddit.com "USERNAME"` -- community reactions
- **Media**: Search `"display_name" product-name review` -- journalist mentions
- **Navigate to Substack comments**: `browser navigate "https://USERNAME.substack.com/p/POST-SLUG/comments"`

## Data Structure

Each post in `posts_detail/` should have:
```json
{
  "id": "tweet_id",
  "url": "https://x.com/...",
  "text": "Full tweet text",
  "timestamp_iso": "2026-01-28T02:28:44.000Z",
  "timestamp_display": "Jan 28",
  "metrics_parsed": {
    "replies": "37",
    "retweets": "83",
    "likes": "1.2K",
    "views": "1.4K"
  },
  "comments": []
}
```

## Known Issues

- **Algorithmic timeline**: Profile page shows popular posts, not recent ones. Always supplement with web search.
- **Login wall**: Comments/replies require X login. Use alternative platforms for audience feedback.
- **Rate limiting**: Add 2-3 second delays between browser navigation requests.
- **Async JS**: Browser console exec doesn't handle async well. Use synchronous extraction scripts + separate scroll commands.
- **Mixed quotes in JS**: Write complex JS to temp files, inject via `$(cat file.js)`.
