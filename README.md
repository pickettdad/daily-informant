# The Daily Informant

**Facts · Sources · Clarity**

A calm, unbiased, fact-focused morning news briefing. Updated once daily at 6 AM EST. No ads, no sponsors, no outrage optimization.

---

## What This Is

An automated news site that:
- Fetches stories from RSS feeds (BBC, Reuters, CBC)
- Extracts neutral facts using AI (OpenAI)
- Publishes a daily morning edition with source links
- Tracks ongoing situations with timeline pages
- Includes a "Good Developments" section for positive news
- Offers an optional reflection/prayer footer

## Tech Stack

- **Frontend**: Next.js 15 (App Router) on Vercel
- **Pipeline**: Python script run by GitHub Actions
- **AI**: OpenAI GPT-4o-mini for fact extraction
- **Data**: Simple JSON files (no database needed)
- **Hosting**: Vercel (free tier)

---

## Setup Guide (Start to Finish)

### Step 1: GitHub

1. Create a new repo on GitHub (e.g., `daily-informant`)
2. **Make it PUBLIC** — this avoids deployment permission issues with Vercel
3. Upload all files from this project to the repo

### Step 2: API Keys & Secrets

In your GitHub repo: **Settings → Secrets and variables → Actions**

Add these secrets:

| Secret Name | What It Is |
|---|---|
| `OPENAI_API_KEY` | Your OpenAI API key from platform.openai.com |
| `GH_PAT` | A GitHub Personal Access Token (fine-grained, Contents: Read/Write, for this repo only) |
| `VERCEL_DEPLOY_HOOK` | A deploy hook URL from Vercel (see Step 3) |

### Step 3: Vercel

1. Go to vercel.com, sign in with GitHub
2. Import your `daily-informant` repo
3. Framework: Next.js (should auto-detect)
4. Deploy — you'll get a live URL
5. In Vercel: **Project Settings → Git → Deploy Hooks**
   - Create a hook named `daily-pipeline`, branch `main`
   - Copy the URL and save it as `VERCEL_DEPLOY_HOOK` in GitHub Secrets

### Step 4: Test the Pipeline

1. Go to your repo → **Actions** tab
2. Click **Morning Pipeline** → **Run workflow**
3. Watch the logs — you should see feeds being fetched and stories extracted
4. Check `data/daily.json` — it should have real AI-generated content
5. Your Vercel site should redeploy automatically

### Step 5: You're Live

The pipeline runs automatically at 6:05 AM EST every day. Your site updates itself.

---

## Project Structure

```
daily-informant/
├── app/                      # Next.js pages
│   ├── layout.tsx            # Shared header, footer, fonts
│   ├── page.tsx              # Homepage (daily edition)
│   ├── topics/
│   │   ├── page.tsx          # All ongoing situations
│   │   └── [slug]/page.tsx   # Individual topic timeline
│   └── how-it-works/
│       └── page.tsx          # Editorial constitution
├── data/
│   ├── daily.json            # Today's edition (auto-updated by pipeline)
│   └── topics.json           # Ongoing situation topics
├── lib/
│   ├── data.ts               # Data loading utilities
│   └── design.ts             # Design tokens
├── scripts/
│   └── generate_daily.py     # The morning pipeline
├── .github/workflows/
│   └── morning.yml           # GitHub Actions schedule
└── package.json
```

## Adding More RSS Sources

Edit `FEEDS` in `scripts/generate_daily.py`:

```python
FEEDS = [
    {"name": "BBC World", "url": "https://feeds.bbci.co.uk/news/world/rss.xml"},
    {"name": "CBC News", "url": "https://www.cbc.ca/webfeed/rss/rss-topstories"},
    # Add more here:
    {"name": "NPR News", "url": "https://feeds.npr.org/1001/rss.xml"},
]
```

## Costs

- **Vercel**: Free (Hobby tier)
- **GitHub Actions**: Free (2,000 mins/month on free plan)
- **OpenAI API**: ~$0.10–$0.50/day for 6 stories with gpt-4o-mini
- **Total**: Under $15/month

---

*Built with care for people who are tired of noise and want signal.*
