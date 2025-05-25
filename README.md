# Web Scraping with LLMs and LangChain

A sophisticated web scraper that uses LangChain and OpenAI's GPT models to intelligently summarize web content. Built with FastAPI, PostgreSQL, and Docker.

## Features

- Asynchronous web scraping with rate limiting
- Intelligent content processing using LangChain and OpenAI
- Structured data storage in PostgreSQL
- RESTful API endpoints with FastAPI
- Containerized deployment with Docker
- Real-time scraping status updates
- Beautiful web interface

## Tech Stack

- **Backend**: FastAPI, Python 3.11
- **Database**: PostgreSQL
- **AI/ML**: LangChain, OpenAI GPT-3.5
- **Containerization**: Docker
- **Web Scraping**: BeautifulSoup4, aiohttp

## Prerequisites

- Docker and Docker Compose
- OpenAI API key
- PostgreSQL (if running locally)

## Setup

1. Clone the repository:
```bash
git clone <your-repo-url>
cd <repo-name>
```

2. Create a `.env` file:
```bash
OPENAI_API_KEY=your_openai_api_key
DATABASE_URL=postgresql://postgres:postgres@db:5432/webscraper
```

3. Build and run with Docker:
```bash
docker-compose up --build
```

4. Access the application:
- Web Interface: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## API Endpoints

- `POST /api/scrape`: Start a new scraping job
- `GET /api/jobs/{job_id}`: Get job status
- `GET /api/content`: Query scraped content

## Database Schema

### ScrapedContent
- `id`: Primary key
- `url`: URL of scraped content
- `title`: Page title
- `text`: Full text content
- `summary`: AI-generated summary
- `extra_metadata`: Additional metadata
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

### ScrapingJob
- `id`: Primary key
- `status`: Job status (pending/running/completed/failed)
- `urls`: List of URLs to scrape
- `results`: Scraping results
- `error`: Error message (if any)
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

## Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run tests:
```bash
pytest
```

3. Format code:
```bash
black .
isort .
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - see LICENSE file for details 