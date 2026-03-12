// Browser console injection script for extracting tweets from X/Twitter profile timeline
// Usage: Inject via `browser console exec` after navigating to a profile page
//
// Returns JSON array of tweet objects from the currently loaded timeline

(function() {
  const tweets = [];
  const seen = new Set();
  document.querySelectorAll('article[data-testid="tweet"]').forEach(article => {
    try {
      const userEl = article.querySelector('[data-testid="User-Name"]');
      const textEl = article.querySelector('[data-testid="tweetText"]');
      const timeEl = article.querySelector('time');
      const linkEl = timeEl ? timeEl.closest('a') : null;
      const statsEl = article.querySelector('[role="group"]');

      const url = linkEl ? linkEl.href : '';
      if (!url || seen.has(url)) return;
      seen.add(url);

      // Extract tweet ID from URL
      const idMatch = url.match(/status\/(\d+)/);
      const id = idMatch ? idMatch[1] : '';

      // Extract metrics from aria-labels
      const metrics = {};
      if (statsEl) {
        statsEl.querySelectorAll('[role="button"], button').forEach(btn => {
          const label = btn.getAttribute('aria-label') || '';
          const match = label.match(/(\d[\d,.KMkm]*)\s*(repl|repost|like|bookmark|view)/i);
          if (match) {
            const key = match[2].toLowerCase().replace('repl', 'replies').replace('repost', 'retweets').replace('like', 'likes').replace('bookmark', 'bookmarks').replace('view', 'views');
            metrics[key] = match[1];
          }
        });
      }

      tweets.push({
        id,
        url,
        user: userEl ? userEl.innerText.split('\n')[0] : '',
        handle: userEl ? (userEl.innerText.match(/@\w+/) || [''])[0] : '',
        text: textEl ? textEl.innerText : '',
        timestamp: timeEl ? timeEl.getAttribute('datetime') : '',
        timestamp_display: timeEl ? timeEl.innerText : '',
        metrics
      });
    } catch(e) {}
  });
  return JSON.stringify(tweets);
})();
