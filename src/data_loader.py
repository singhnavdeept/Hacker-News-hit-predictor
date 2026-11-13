"""
Data loader and feature extraction module for Hacker News HIT Predictor.
Fetches real HN posts or generates a realistic benchmark dataset for training.
"""

import os
import re
import random
import datetime
from urllib.parse import urlparse
import pandas as pd
import requests

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DATA_FILE = os.path.join(DATA_DIR, "hn_posts.csv")

DOMAIN_CATEGORIES = {
    "github": ["github.com", "gitlab.com"],
    "tech_media": ["techcrunch.com", "arstechnica.com", "theverge.com", "wired.com", "bloomberg.com", "reuters.com", "nytimes.com"],
    "blogs": ["medium.com", "substack.com", "wordpress.com", "dev.to", "hashnode.com"],
    "paper": ["arxiv.org", "biorxiv.org", "nature.com"],
}

def extract_domain_type(url: str) -> str:
    if not url or pd.isna(url) or url.strip() == "":
        return "self"
    try:
        netloc = urlparse(url).netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        for cat, domains in DOMAIN_CATEGORIES.items():
            for d in domains:
                if d in netloc:
                    return cat
        return "external"
    except Exception:
        return "unknown"

def enrich_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "submission_time" in df.columns:
        df["submission_time"] = pd.to_datetime(df["submission_time"], errors="coerce", utc=True)
        df["submission_hour"] = df["submission_time"].dt.hour.fillna(14).astype(int)
        df["submission_day"] = df["submission_time"].dt.dayofweek.fillna(2).astype(int)
    else:
        if "submission_hour" not in df.columns:
            df["submission_hour"] = 14
        if "submission_day" not in df.columns:
            df["submission_day"] = 2

    df["title"] = df["title"].fillna("").astype(str)
    df["title_len"] = df["title"].apply(len)
    df["title_word_count"] = df["title"].apply(lambda t: len(t.split()))
    
    if "url" in df.columns:
        df["domain_type"] = df["url"].apply(extract_domain_type)
    else:
        df["domain_type"] = "self"

    if "score" in df.columns:
        df["is_hit"] = (df["score"] >= 50).astype(int)

    return df

def generate_synthetic_benchmark(n_samples: int = 3000) -> pd.DataFrame:
    """
    Generates a realistic dataset modeled on Hacker News submission patterns.
    """
    random.seed(42)

    hit_templates = [
        ("Show HN: {tool} – An open-source {desc}", "github", 50, 600),
        ("Show HN: I built a fast {desc} in Rust", "github", 70, 850),
        ("Why SQLite is so fast and reliable", "blogs", 80, 1100),
        ("PostgreSQL 17 Released", "tech_media", 100, 1500),
        ("Linux Kernel 6.12 adds major memory improvements", "tech_media", 60, 900),
        ("Reflections on 10 years building bootstrapped SaaS", "blogs", 55, 750),
        ("Reverse engineering the Apple M4 chip architecture", "blogs", 85, 1200),
        ("Why we switched from AWS to bare-metal servers", "blogs", 120, 1800),
        ("Ask HN: What books changed the way you think about code?", "self", 65, 850),
        ("DeepSeek-R1: Open reasoning models at scale", "paper", 150, 2200),
        ("FastHTML – Modern web applications in pure Python", "github", 90, 1300),
        ("The architectural design of distributed systems", "paper", 50, 500),
        ("FAA grounds flights nationwide due to system outage", "tech_media", 200, 2500),
        ("Cloudflare outage post-mortem: Root cause analysis", "tech_media", 140, 2100),
        ("Ask HN: Favorite software tools that just work?", "self", 60, 950),
    ]

    flop_templates = [
        ("Top 5 Crypto trading signals for today", "blogs", 1, 6),
        ("Best SEO agency for growing your small business", "blogs", 1, 4),
        ("My daily productivity routine as an entrepreneur", "blogs", 2, 18),
        ("Check out my brand new landing page template", "github", 1, 12),
        ("Why NFT games are the future of entertainment", "tech_media", 1, 8),
        ("10 quick tips to master Python in 15 minutes", "blogs", 2, 22),
        ("Buy low sell high: Crypto automated trading bot", "github", 1, 9),
        ("We are hiring React developers in Mumbai", "blogs", 1, 5),
        ("Marketing hacks to get 10,000 users overnight", "blogs", 1, 14),
        ("Check this link", "external", 1, 3),
        ("A short question about my personal computer setup", "self", 1, 10),
        ("Discount coupons for web hosting services", "external", 1, 2),
        ("Is Java better than PHP? Thoughts?", "self", 3, 25),
        ("Exciting press release: Company announces seed round", "tech_media", 2, 19),
        ("Random thoughts on modern web development frameworks", "blogs", 2, 24),
    ]

    tools = ["LlamaSearch", "DuckDB-Viewer", "DockerMon", "RustKV", "TinyCache", "MicroLens", "GitTrace"]
    descs = ["vector database", "terminal monitor", "distributed lock manager", "fast markdown engine", "code search indexer"]

    domains_map = {
        "github": ["https://github.com/developer/project", "https://gitlab.com/dev/tool"],
        "tech_media": ["https://arstechnica.com/tech-policy/story", "https://techcrunch.com/features/article", "https://nytimes.com/tech/update"],
        "blogs": ["https://medium.com/engineering-deepdive", "https://danluu.com/analysis", "https://blog.cloudflare.com/incident"],
        "paper": ["https://arxiv.org/abs/2401.0001", "https://nature.com/articles/s41586-024"],
        "self": ["", ""],
        "external": ["https://example-site.org/post", "https://my-marketing-hub.net/deal"],
    }

    records = []
    base_date = datetime.datetime(2026, 1, 1, 0, 0, 0)

    for i in range(n_samples):
        is_hit_sample = random.random() < 0.28  # ~28% hit rate (realistic for frontpage/high score)
        if is_hit_sample:
            tmpl, d_type, min_s, max_s = random.choice(hit_templates)
            title = tmpl.format(tool=random.choice(tools), desc=random.choice(descs))
            score = random.randint(min_s, max_s)
            # Hits tend to be posted during peak HN hours (13:00 to 19:00 UTC) on weekdays
            hour = random.choice([13, 14, 15, 16, 17, 18, 19, 12, 11, random.randint(0, 23)])
            day = random.choice([0, 1, 2, 3, 4, random.randint(0, 6)])
        else:
            tmpl, d_type, min_s, max_s = random.choice(flop_templates)
            title = tmpl.format(tool=random.choice(tools), desc=random.choice(descs))
            score = random.randint(min_s, max_s)
            hour = random.randint(0, 23)
            day = random.randint(0, 6)

        url = random.choice(domains_map[d_type])
        delta_days = random.randint(0, 300)
        dt = base_date + datetime.timedelta(days=delta_days, hours=hour, minutes=random.randint(0, 59))

        records.append({
            "id": 1000000 + i,
            "title": title,
            "url": url,
            "score": score,
            "submission_time": dt.isoformat(),
        })

    df = pd.DataFrame(records)
    return enrich_features(df)

def load_or_create_dataset(force_synthetic: bool = False) -> pd.DataFrame:
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(DATA_FILE) and not force_synthetic:
        df = pd.read_csv(DATA_FILE)
        return enrich_features(df)

    # Try fetching latest top stories from HN Algolia API if connected, else fallback to benchmark
    try:
        if not force_synthetic:
            print("Fetching sample Hacker News posts from Algolia API...")
            resp = requests.get(
                "https://hn.algolia.com/api/v1/search?tags=story&hitsPerPage=100",
                timeout=5
            )
            if resp.status_code == 200:
                hits = resp.json().get("hits", [])
                if len(hits) >= 50:
                    records = []
                    for h in hits:
                        records.append({
                            "id": h.get("objectID"),
                            "title": h.get("title", ""),
                            "url": h.get("url", ""),
                            "score": h.get("points", 0) or 0,
                            "submission_time": h.get("created_at", datetime.datetime.utcnow().isoformat())
                        })
                    df_live = pd.DataFrame(records)
                    df_syn = generate_synthetic_benchmark(n_samples=2500)
                    df = pd.concat([df_live, df_syn], ignore_index=True)
                    df = enrich_features(df)
                    df.to_csv(DATA_FILE, index=False)
                    print(f"Dataset successfully created with {len(df)} records.")
                    return df
    except Exception as exc:
        print(f"Online fetch skipped ({exc}), generating benchmark dataset...")

    df = generate_synthetic_benchmark(n_samples=3000)
    df.to_csv(DATA_FILE, index=False)
    print(f"Benchmark dataset saved to {DATA_FILE} with {len(df)} records.")
    return df

if __name__ == "__main__":
    df = load_or_create_dataset()
    print("Dataset Summary:")
    print(f"Total rows: {len(df)}")
    print(f"Hit distribution (score >= 50):\n{df['is_hit'].value_counts(normalize=True)}")
