# X-Tweet-Fetcher Capabilities

**Source:** [https://github.com/ythx-101/x-tweet-fetcher/](https://github.com/ythx-101/x-tweet-fetcher/)

This skill provides powerful, zero-API-key data fetching and monitoring capabilities across X (Twitter) and various Chinese platforms. The following capabilities are abstracted from the project's CHANGELOG.

## Core Capabilities

### 1. X (Twitter) Data Fetching
- **Single Tweet Fetching**: Fetch tweets via FxTwitter API without any dependencies or API keys.
- **Reply Threads & Nested Replies**: Extract tweet replies, including nested thread replies and links in the comment section.
- **User Timeline**: Fetch user timelines with support for pagination (up to 200+ tweets) and correct chronological sorting (Snowflake ID).
- **X Lists**: Fetch tweets from specific X Lists using list IDs or URLs, with pagination support.
- **X Articles & Quoted Tweets**: Full-text extraction for long-form X Articles and automatic inclusion of quoted tweets and retweet tracking.

### 2. Mentions & Growth Monitoring
- **Real-time Mentions Monitoring**: Monitor who mentioned specific users (`@username`) using Google Search via Camofox, without needing an API key. Includes incremental detection and cron integration.
- **Nitter Mentions**: Real-time X mention monitoring based on Nitter.

### 3. Chinese Platform Support
- **Multi-Platform Fetching**: Support for extracting content from Weibo (posts, comments, stats), Bilibili (video info, stats, danmaku), CSDN (articles, code blocks), and Xiaohongshu (via proxy/cookies).
- **WeChat Articles & Search**: Fetch WeChat official account articles directly. Supports Sogou WeChat search with real URL resolution via Google/DDG and SSH proxy capabilities.
- **Auto-Detection**: Automatically detects the platform based on the provided URL.

### 4. Advanced Technical Features
- **Camofox & Nitter Integration**: Uses Camofox (anti-detect browser) and Nitter for privacy-respecting, zero-cost data extraction.
- **Proxy Support**: Built-in support for SSH proxies and 24/7 home router proxies.
- **Flexible Output Formats**: Export data in JSON, Markdown (with YAML frontmatter), or plain text.
- **Robust Parsing**: Advanced regex and error tolerance for extracting stats, icons, and nested content correctly.
