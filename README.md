# Web Scraper with AI Summaries

A web scraper that extracts content from websites and creates concise summaries using AI. Built with modern tools for reliability and speed.

## What It Does

- Scrapes web pages quickly and efficiently
- Creates clear summaries of web content
- Stores everything in a database for easy access
- Shows real-time progress of scraping jobs
- Works with any website
- Clean, modern web interface

## Built With

- FastAPI - Fast web framework
- PostgreSQL - Reliable database
- LangChain & GPT-3.5 - For smart summaries
- Docker - Easy deployment
- BeautifulSoup4 - Web scraping
- aiohttp - Fast async requests

## Getting Started

### What You Need

- Docker and Docker Compose
- OpenAI API key
- PostgreSQL (optional for local development)

### Quick Start

1. Get the code:
```bash
git clone <your-repo-url>
cd <repo-name>
```

2. Set up your environment:
```bash
# Create .env file with:
OPENAI_API_KEY=your_openai_api_key
DATABASE_URL=postgresql://postgres:postgres@db:5432/webscraper
```

3. Run it:
```bash
docker-compose up --build
```

4. Open in your browser:
- Main app: http://localhost:8000
- API docs: http://localhost:8000/docs

## How to Use

### API Endpoints

- `POST /api/scrape` - Start scraping a website
- `GET /api/jobs/{job_id}` - Check scraping progress
- `GET /api/content` - Get scraped content

### Database Structure

#### ScrapedContent
- `id` - Unique identifier
- `url` - Website address
- `title` - Page title
- `text` - Full content
- `summary` - AI summary
- `extra_metadata` - Additional info
- `created_at` - When it was scraped
- `updated_at` - Last update time

#### ScrapingJob
- `id` - Job identifier
- `status` - Current status
- `urls` - Websites to scrape
- `results` - Scraping results
- `error` - Any errors
- `created_at` - Start time
- `updated_at` - Last update

## For Developers

1. Install requirements:
```bash
pip install -r requirements.txt
```

2. Run tests:
```bash
pytest
```

3. Format your code:
```bash
black .
isort .
```

## Want to Help?

1. Fork the repo
2. Make your changes
3. Send a pull request

## License

MIT License - see LICENSE file for details 