# Crypto Alert Bot 🤖

**AI-Powered Crypto News Alerting via Telegram** — with immutable audit trail stored on Shelby Protocol.

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python)
![Telegram](https://img.shields.io/badge/Telegram-Bot-blue?style=for-the-badge&logo=telegram)
![Shelby](https://img.shields.io/badge/Shelby-Protocol-purple?style=for-the-badge)

---

## Overview

Crypto Alert Bot monitors news from multiple sources, analyzes sentiment and impact using AI, and sends alerts directly to your Telegram — with every alert stored permanently on Shelby Protocol.

```
┌─────────────────────────────────────────────────────────────────┐
│                        CRYPTO ALERT BOT                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐    │
│   │  NewsAPI    │  │ CryptoPanic │  │      Reddit RSS     │    │
│   │  CoinGecko  │  │   Twitter   │  │   (CryptoSubs)      │    │
│   └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘    │
│          │                 │                     │               │
│          └─────────────────┼─────────────────────┘               │
│                            ▼                                      │
│                   ┌────────────────┐                              │
│                   │  Aggregator   │  (Dedup + Sort)             │
│                   └────────┬───────┘                              │
│                            ▼                                      │
│                   ┌────────────────┐                              │
│                   │ Sentiment +    │  VADER Sentiment            │
│                   │ Impact Analyze │  Keyword Detection          │
│                   │                │  Source Authority          │
│                   └────────┬───────┘                              │
│                            ▼                                      │
│                   ┌────────────────┐                              │
│                   │ Impact Filter │  Score >= threshold?         │
│                   └────────┬───────┘                              │
│                            ▼                                      │
│          ┌──────────────────┼──────────────────┐                 │
│          ▼                                     ▼                 │
│   ┌──────────────┐                   ┌──────────────┐           │
│   │   Telegram   │                   │    Shelby    │           │
│   │    Alert     │                   │    Blob      │           │
│   │   (HTML)     │                   │   Storage    │           │
│   └──────────────┘                   └──────────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Features

- [x] **Multi-Source News Aggregation** — NewsAPI, CryptoPanic, Reddit RSS, CoinGecko News
- [x] **AI Sentiment Analysis** — VADER sentiment scoring (-1 to +1)
- [x] **Impact Scoring** — Keyword impact + source authority + recency
- [x] **Token Detection** — Auto-detects Bitcoin, Ethereum, Solana, DeFi tokens
- [x] **Beautiful Telegram Alerts** — HTML-formatted with emojis, impact badges
- [x] **Shelby Protocol Storage** — Every alert stored as immutable blob
- [x] **Rate Limiting** — Configurable max alerts per hour
- [x] **Flexible Configuration** — Tokens, keywords, thresholds all configurable

---

## Supported News Sources

| Source | Type | Auth Required |
|--------|------|-------------|
| NewsAPI | General news API | API key (free tier) |
| CryptoPanic | Crypto aggregator | Optional |
| Reddit RSS | Community posts | None |
| CoinGecko News | Crypto-specific | None |

---

## Supported Tokens / Chains

- Bitcoin (BTC)
- Ethereum (ETH)
- Solana (SOL)
- BNB Chain (BNB)
- Cardano (ADA)
- Polygon (MATIC)
- Avalanche (AVAX)
- Chainlink (LINK)
- Uniswap (UNI)
- Aave (AAVE)

---

## Getting Started

### Prerequisites

- Python 3.10+
- Telegram Bot Token (via @BotFather)
- Shelby API Key (via gomi.dev)
- NewsAPI Key (optional, via newsapi.org)

### Installation

```bash
# Clone the repository
git clone https://github.com/tsanli/crypto-alert-bot.git
cd crypto-alert-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Download NLTK data (for sentiment)
python -c "import nltk; nltk.download('vader_lexicon')"
```

### Configuration

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Telegram (required)
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=-1001234567890

# Shelby Protocol (required for storage)
SHELBY_API_KEY=shelby_xxx

# News Sources (optional)
NEWS_API_KEY=your_newsapi_key

# Alert Settings
ALERT_INTERVAL_MINUTES=5
MIN_IMPACT_SCORE=0.5
MAX_ALERTS_PER_HOUR=20

# Monitored Tokens
MONITORED_TOKENS=bitcoin,ethereum,solana,binance,cardano,polygon,avalanche-2,chainlink,uniswap,aave

# Monitored Keywords
MONITORED_KEYWORDS=SEC,ETF,approval,hack,exploit,regulation,ban,delist,partnership
```

### Get Your Credentials

**Telegram Bot:**
1. Open Telegram and chat with @BotFather
2. Send `/newbot`
3. Follow prompts, get your bot token
4. Start a chat with your bot, then send `/start`
5. Get your chat ID via @userinfobot or from the URL

**Shelby API Key:**
1. Visit gomi.dev
2. Create project → Generate API key
3. Select "Shelby" network and enable client usage

**NewsAPI Key:**
1. Visit newsapi.org
2. Sign up for free account
3. Copy your API key

### Run

```bash
# Run once (for testing)
python -m src.main --once

# Run scheduled (continuous)
python -m src.main
```

---

## Alert Format

Alerts are sent as beautiful HTML messages:

```
🚨 EXTREME IMPACT 🟢 POSITIVE

[SEC Approves Spot Bitcoin ETF - Historic Day for Crypto]

The SEC has officially approved multiple spot Bitcoin ETF applications...

━━━━━━━━━━━━━━━
📰 Source: CoinDesk
⏰ Jan 15 at 14:30 UTC
💰 ₿, Ξ  BITCOIN, ETHEREUM
🏷️ #SEC #ETF #approval

Impact: 0.87 | Sentiment: 0.65
```

---

## Project Structure

```
crypto-alert-bot/
├── src/
│   ├── main.py              # Entry point
│   ├── config/
│   │   └── __init__.py     # Configuration management
│   ├── news/
│   │   └── sources.py       # News source integrations
│   ├── sentiment/
│   │   └── analyzer.py      # Sentiment & impact analysis
│   ├── alerts/
│   │   └── dispatcher.py   # Telegram alert formatting & sending
│   └── storage/
│       └── shelby_store.py  # Shelby Protocol blob storage
├── data/                    # Local state & alert logs
├── .env.example
├── requirements.txt
├── README.md
└── LICENSE
```

---

## How It Works

### 1. News Aggregation
Fetches from 4 sources simultaneously, deduplicates, sorts by recency.

### 2. Sentiment Analysis
Uses VADER (Valence Aware Dictionary and sEntiment Reasoner) to calculate compound sentiment score from -1 (negative) to +1 (positive).

### 3. Impact Scoring
Combines multiple signals:
- **Keyword impact** (0-0.4): "hack", "SEC", "ETF" = high impact
- **Source authority** (0-0.25): CoinDesk > Reddit > generic RSS
- **Sentiment extremity** (0-0.2): Extreme sentiment = higher impact
- **Token relevance** (0-0.15): More tokens mentioned = higher score

### 4. Alert Dispatch
Sends HTML-formatted alert to Telegram with:
- Impact badge (LOW/MEDIUM/HIGH/EXTREME)
- Sentiment indicator
- Detected tokens and keywords
- Source and timestamp
- Impact/sentiment scores

### 5. Shelby Storage
Every alert stored as JSON blob on Shelby Protocol:
- Immutable timestamp
- Full article metadata
- Scores and detections
- Message delivery status

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.10+ |
| Bot Framework | python-telegram-bot |
| HTTP Client | httpx |
| Sentiment | VADER (NLTK) |
| RSS Parsing | feedparser |
| Scheduling | asyncio |
| Storage | Shelby Protocol SDK |
| Deployment | VPS, Railway, Render |

---

## Why Shelby?

Every crypto alert is a data point with value. By storing alerts on Shelby Protocol:

- **Immutable history** — Alerts can't be modified or deleted
- **Timestamped proof** — Prove you received an alert at a specific time
- **Decentralized** — No single point of failure
- **Verifiable** — Audit trail of all alerts ever sent

This creates a permanent, auditable record of market-moving events.

---

## License

MIT License — see [LICENSE](LICENSE)

---

**Built with 🤖 for the crypto community**
