# OpinionLense 🔍

A powerful Python tool for scraping and analyzing YouTube comments at scale. OpinionLense enables researchers, data scientists, and content creators to collect, process, and analyze YouTube comments for sentiment analysis, trend detection, and audience insights.

## ✨ Features

- **Scalable Comment Scraping**: Fetch 100k+ comments with robust pagination and automatic retry logic
- **Flexible Video Discovery**: Search by keywords/queries or provide direct video IDs
- **Comprehensive Data Collection**: Captures comments, replies, metadata (likes, timestamps, authors)
- **Smart Deduplication**: Automatic comment ID tracking to prevent duplicates
- **Resumable Operations**: Checkpoint system allows resuming interrupted scrapes
- **Text Preprocessing**: Built-in cleaning and normalization utilities
- **Real-time Updates**: Fetch only new comments since last check
- **Rate Limit Handling**: Exponential backoff for API quota management
- **Export to CSV**: Clean, structured data ready for analysis

## 📋 Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Quick Start](#quick-start)
  - [Scalable Scraping](#scalable-scraping)
  - [Search-Based Collection](#search-based-collection)
  - [Real-time Monitoring](#real-time-monitoring)
- [Project Structure](#project-structure)
- [API Quotas](#api-quotas)
- [Examples](#examples)
- [Contributing](#contributing)
- [License](#license)

## 🚀 Installation

### Prerequisites

- Python 3.7 or higher
- YouTube Data API v3 key ([Get one here](https://console.developers.google.com/))

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/YasirAhmed2/OpinionLense.git
   cd OpinionLense
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API credentials**
   
   Create a `.env` file in the project root:
   ```bash
   YOUTUBE_API_KEY=your_api_key_here
   ```

## ⚙️ Configuration

### Getting YouTube API Key

1. Go to [Google Cloud Console](https://console.developers.google.com/)
2. Create a new project or select an existing one
3. Enable the **YouTube Data API v3**
4. Create credentials (API Key)
5. Copy the API key to your `.env` file

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `YOUTUBE_API_KEY` | Your YouTube Data API v3 key | Yes |

## 📖 Usage

### Quick Start

Fetch comments from a single video:

```python
from main import run

# Using video URL
run("https://www.youtube.com/watch?v=dQw4w9WgXcQ", limit=500)

# Using video ID directly
run("dQw4w9WgXcQ", limit=500)
```

This saves comments to `data/raw_comments.csv` by default.

### Scalable Scraping

For large-scale data collection (100k+ comments):

#### 1. Search by Keywords

Create a `queries.txt` file with search terms (one per line):
```
AI
machine learning
tech review
```

Then run:
```bash
python scrape_youtube.py \
  --queries queries.txt \
  --videos-per-query 200 \
  --max-comments-per-video 2000 \
  --out data/youtube_comments.csv
```

#### 2. Direct Video IDs

```bash
python scrape_youtube.py \
  --video-ids "dQw4w9WgXcQ,kn0IZelsCoM" \
  --max-comments-per-video 5000 \
  --out data/youtube_comments.csv
```

#### Advanced Options

```bash
python scrape_youtube.py \
  --queries queries.txt \
  --videos-per-query 200 \
  --max-comments-per-video 2000 \
  --out data/youtube_comments.csv \
  --checkpoint data/checkpoints/processed_videos.csv \
  --order relevance \
  --region US \
  --published-after 2024-01-01T00:00:00Z
```

**Parameters:**
- `--queries`: Path to file with search queries (one per line)
- `--video-ids`: Comma-separated video IDs to scrape
- `--videos-per-query`: Max videos to fetch per query (default: 200)
- `--max-comments-per-video`: Max comments per video (default: 2000)
- `--out`: Output CSV path (default: `data/youtube_comments.csv`)
- `--checkpoint`: Checkpoint file for resumable scrapes
- `--order`: Search ordering (`relevance`, `date`, `viewCount`, `rating`)
- `--region`: Region code filter (e.g., `US`, `GB`, `PK`)
- `--published-after`: ISO-8601 date filter (e.g., `2024-01-01T00:00:00Z`)

### Text Preprocessing

Clean and prepare comments for analysis:

```python
from utils.preprocess import preprocess_dataset

# Clean comments and create train/test splits
train, test = preprocess_dataset(
    input_path="data/raw_comments.csv",
    output_dir="data",
    sample_size=100000  # Optional: limit dataset size
)
```

This performs:
- Lowercase conversion
- URL/mention/hashtag removal
- Punctuation and number removal
- Whitespace normalization
- Train/test split (80/20)

### Real-time Monitoring

Fetch only new comments since last check:

```python
from utils.realtime import fetch_new_since, iso_now

# Store current timestamp
last_check = iso_now()

# Later, fetch only new comments
new_comments = fetch_new_since(
    video_id="dQw4w9WgXcQ",
    since_iso=last_check,
    max_total=500
)
```

## 📁 Project Structure

```
OpinionLense/
├── main.py                      # Simple single-video scraper
├── scrape_youtube.py            # Scalable multi-video scraper
├── config.py                    # API key configuration
├── requirements.txt             # Python dependencies
├── queries.txt                  # Sample search queries
├── .env                         # API credentials (create this)
│
├── utils/
│   ├── youtube_api.py          # Core YouTube API wrapper
│   ├── url.py                  # Video ID extraction utilities
│   ├── preprocess.py           # Text cleaning and preprocessing
│   └── realtime.py             # Real-time comment fetching
│
├── data/
│   ├── raw_comments.csv        # Scraped comments output
│   └── checkpoints/            # Resume state tracking
│
├── results/
│   └── sentiment_summary.json  # Analysis outputs
│
└── notebooks/
    └── eda.ipynb               # Exploratory data analysis
```

## 📊 Output Format

Scraped comments are saved as CSV with the following columns:

| Column | Description |
|--------|-------------|
| `comment_id` | Unique YouTube comment ID |
| `video_id` | Associated video ID |
| `parent_id` | Parent comment ID (for replies) |
| `is_reply` | Boolean indicating if comment is a reply |
| `author` | Comment author's display name |
| `text` | Comment text content |
| `likes` | Number of likes |
| `published_at` | ISO-8601 publication timestamp |
| `updated_at` | ISO-8601 last update timestamp |
| `reply_count` | Number of replies to this comment |

## 🔧 API Quotas

The YouTube Data API v3 has daily quotas:
- **Default quota**: 10,000 units/day
- **Comment fetch**: ~1 unit per comment thread
- **Search**: 100 units per search request

**Tips to maximize quota efficiency:**
- Use checkpointing to avoid re-scraping
- Enable deduplication
- Batch operations when possible
- Monitor quota usage in [Google Cloud Console](https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas)

## 💡 Examples

### Example 1: Collect Tech Review Comments

```python
# Scrape tech review videos and analyze sentiment
from main import run

run("https://www.youtube.com/watch?v=VIDEO_ID", 
    out_path="data/tech_reviews.csv", 
    limit=1000)
```

### Example 2: Monitor Product Launch

```bash
# Track comments on new product launches
python scrape_youtube.py \
  --queries "iPhone 15 review" \
  --videos-per-query 50 \
  --max-comments-per-video 500 \
  --published-after 2024-09-01T00:00:00Z \
  --out data/iphone_launch.csv
```

### Example 3: Multi-Topic Analysis

Create `topics.txt`:
```
climate change
renewable energy
electric vehicles
```

```bash
python scrape_youtube.py \
  --queries topics.txt \
  --videos-per-query 100 \
  --max-comments-per-video 1000 \
  --order date \
  --out data/climate_discussion.csv
```

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/AmazingFeature`)
3. **Commit your changes** (`git commit -m 'Add some AmazingFeature'`)
4. **Push to the branch** (`git push origin feature/AmazingFeature`)
5. **Open a Pull Request**

### Development Guidelines

- Follow PEP 8 style guidelines
- Add docstrings to new functions
- Test your changes thoroughly
- Update documentation as needed

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## ⚠️ Disclaimer

- Respect YouTube's Terms of Service when scraping data
- Be mindful of API rate limits
- Use collected data responsibly and ethically
- Do not use for spam or malicious purposes
- Consider privacy implications when handling user-generated content

## 🙏 Acknowledgments

- Built using the [Google API Python Client](https://github.com/googleapis/google-api-python-client)
- Powered by YouTube Data API v3

## 📧 Contact

For questions, issues, or suggestions:
- **GitHub Issues**: [Create an issue](https://github.com/YasirAhmed2/OpinionLense/issues)
- **Repository**: [YasirAhmed2/OpinionLense](https://github.com/YasirAhmed2/OpinionLense)

---

**Happy Scraping! 🎉**
