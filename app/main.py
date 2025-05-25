from typing import List
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session
from datetime import datetime
import os

from app.core.scraper import AsyncWebScraper
from app.db.models import ScrapedContent, ScrapingJob, Base
from app.db.database import get_db, engine

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Web Scraping with LLMs and LangChain")

# Create static directory if it doesn't exist
os.makedirs("app/static", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <head>
            <title>Web Scraping with LLMs and LangChain</title>
            <link rel="icon" type="image/png" href="/static/favicon.png">
            <link rel="shortcut icon" type="image/png" href="/static/favicon.png">
            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    line-height: 1.6;
                }
                h1 { color: #2c3e50; }
                .endpoint {
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 10px 0;
                }
                code {
                    background: #e9ecef;
                    padding: 2px 5px;
                    border-radius: 3px;
                }
                .form-container {
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 5px;
                    margin: 20px 0;
                }
                .url-input {
                    width: 100%;
                    padding: 10px;
                    margin: 10px 0;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                }
                .submit-btn {
                    background: #2c3e50;
                    color: white;
                    padding: 10px 20px;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                }
                .submit-btn:hover {
                    background: #34495e;
                }
                .results {
                    margin-top: 20px;
                    display: none;
                }
                .loading {
                    display: none;
                    text-align: center;
                    margin: 20px 0;
                }
                .error {
                    color: #dc3545;
                    display: none;
                    margin: 10px 0;
                }
                .log-container {
                    background: #2c3e50;
                    color: #fff;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                    font-family: monospace;
                    max-height: 300px;
                    overflow-y: auto;
                }
                .log-entry {
                    margin: 5px 0;
                    padding: 5px;
                    border-bottom: 1px solid #34495e;
                }
                .log-time {
                    color: #95a5a6;
                    margin-right: 10px;
                }
                .log-info { color: #3498db; }
                .log-success { color: #2ecc71; }
                .log-warning { color: #f1c40f; }
                .log-error { color: #e74c3c; }
            </style>
        </head>
        <body>
            <h1>Welcome to Intelligent Web Scraper API!</h1>
            <p>This API provides endpoints for intelligent web scraping with content analysis.</p>
            
            <div class="form-container">
                <h2>Scrape a Website</h2>
                <form id="scrapeForm">
                    <input type="url" id="urlInput" class="url-input" placeholder="Enter URL to scrape (e.g., https://example.com)" required>
                    <button type="submit" class="submit-btn">Start Scraping</button>
                </form>
                <div id="error" class="error"></div>
                <div id="loading" class="loading">Scraping in progress... Please wait.</div>
            </div>

            <div id="logContainer" class="log-container" style="display: none;">
                <h3>Process Log</h3>
                <div id="logContent"></div>
            </div>

            <div id="results" class="results">
                <h2>Scraping Results</h2>
                <div id="content"></div>
            </div>

           
            
            <script>
                function addLogEntry(message, type = 'info') {
                    const logContainer = document.getElementById('logContainer');
                    const logContent = document.getElementById('logContent');
                    const now = new Date();
                    const timeStr = now.toLocaleTimeString();
                    
                    const entry = document.createElement('div');
                    entry.className = `log-entry log-${type}`;
                    entry.innerHTML = `<span class="log-time">[${timeStr}]</span> ${message}`;
                    
                    logContent.appendChild(entry);
                    logContainer.scrollTop = logContainer.scrollHeight;
                }

                function validateUrl(url) {
                    try {
                        new URL(url);
                        return true;
                    } catch {
                        return false;
                    }
                }

                document.getElementById('scrapeForm').addEventListener('submit', async (e) => {
                    e.preventDefault();
                    const urlInput = document.getElementById('urlInput');
                    const loading = document.getElementById('loading');
                    const error = document.getElementById('error');
                    const results = document.getElementById('results');
                    const content = document.getElementById('content');
                    const logContainer = document.getElementById('logContainer');
                    const logContent = document.getElementById('logContent');

                    // Reset UI
                    error.style.display = 'none';
                    results.style.display = 'none';
                    loading.style.display = 'block';
                    content.innerHTML = '';
                    logContent.innerHTML = '';
                    logContainer.style.display = 'block';

                    try {
                        const url = urlInput.value.trim();
                        
                        if (!validateUrl(url)) {
                            throw new Error('Please enter a valid URL');
                        }

                        addLogEntry('Starting new scraping job...', 'info');
                        addLogEntry(`Target URL: ${url}`, 'info');

                        // Start scraping job
                        addLogEntry('Sending request to start scraping...', 'info');
                        const scrapeResponse = await fetch('/api/scrape', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                urls: [url]
                            })
                        });

                        if (!scrapeResponse.ok) {
                            const errorData = await scrapeResponse.json();
                            throw new Error(errorData.detail || 'Failed to start scraping job');
                        }

                        const { job_id } = await scrapeResponse.json();
                        addLogEntry(`Job created with ID: ${job_id}`, 'success');
                        
                        // Polling with exponential backoff
                        let attempts = 0;
                        const maxAttempts = 40; // 30 seconds maximum
                        const baseDelay = 1000; // Start with 1 second
                        
                        while (attempts < maxAttempts) {
                            addLogEntry(`Checking job status (Attempt ${attempts + 1}/${maxAttempts})...`, 'info');
                            const statusResponse = await fetch(`/api/jobs/${job_id}`);
                            
                            if (!statusResponse.ok) {
                                throw new Error('Failed to check job status');
                            }
                            
                            const jobStatus = await statusResponse.json();

                            if (jobStatus.status === 'completed') {
                                addLogEntry('Job completed successfully!', 'success');
                                addLogEntry('Fetching scraped content...', 'info');
                                
                                // Get the scraped content for this specific URL
                                const contentResponse = await fetch(`/api/content?url=${encodeURIComponent(url)}`);
                                if (!contentResponse.ok) {
                                    throw new Error('Failed to fetch content');
                                }
                                
                                const contentData = await contentResponse.json();
                                
                                if (contentData && contentData.length > 0) {
                                    const data = contentData[0];
                                    addLogEntry('Content retrieved successfully', 'success');
                                    
                                    // Display only this result
                                    content.innerHTML = `
                                        <div class="endpoint">
                                            <h3>Title</h3>
                                            <p>${data.title || 'N/A'}</p>
                                            
                                            <h3>Content</h3>
                                            <p>${data.text || 'N/A'}</p>
                                            
                                            <h3>Summary</h3>
                                            <p>${data.summary || 'N/A'}</p>
                                            
                                            <h3>URL</h3>
                                            <p><a href="${data.url}" target="_blank">${data.url}</a></p>
                                            
                                            <h3>Timestamp</h3>
                                            <p>${new Date(data.created_at).toLocaleString()}</p>
                                        </div>
                                    `;
                                    results.style.display = 'block';
                                    addLogEntry('Results displayed successfully', 'success');
                                } else {
                                    addLogEntry('No content found in the response', 'warning');
                                }
                                break;
                            } else if (jobStatus.status === 'failed') {
                                addLogEntry(`Job failed: ${jobStatus.error || 'Unknown error'}`, 'error');
                                throw new Error(jobStatus.error || 'Scraping failed');
                            } else {
                                addLogEntry(`Current status: ${jobStatus.status}`, 'info');
                            }

                            // Calculate delay with exponential backoff
                            const delay = Math.min(baseDelay * Math.pow(1.5, attempts), 5000); // Max 5 seconds
                            addLogEntry(`Waiting ${Math.round(delay/1000)} seconds before next check...`, 'info');
                            await new Promise(resolve => setTimeout(resolve, delay));
                            attempts++;
                        }

                        if (attempts >= maxAttempts) {
                            addLogEntry('Scraping timed out after 30 seconds', 'error');
                            throw new Error('Scraping timed out after 30 seconds');
                        }
                    } catch (err) {
                        addLogEntry(`Error: ${err.message}`, 'error');
                        error.textContent = err.message;
                        error.style.display = 'block';
                    } finally {
                        loading.style.display = 'none';
                        addLogEntry('Process completed', 'info');
                    }
                });
            </script>
        </body>
    </html>
    """

@app.get("/favicon.png")
async def favicon():
    return FileResponse("app/static/favicon.png")

class ScrapeRequest(BaseModel):
    urls: List[HttpUrl]

class ScrapeResponse(BaseModel):
    job_id: int
    status: str
    message: str

@app.post("/api/scrape", response_model=ScrapeResponse)
async def create_scraping_job(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    try:
        # Create new job
        job = ScrapingJob(
            status="pending",
            urls=[str(url) for url in request.urls],
            results=[]
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        # Start scraping in background
        background_tasks.add_task(process_scraping_job, job.id, [str(url) for url in request.urls])
        
        return ScrapeResponse(
            job_id=job.id,
            status="pending",
            message="Scraping job created successfully"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: int, db: Session = Depends(get_db)):
    job = db.query(ScrapingJob).filter(ScrapingJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.get("/api/content")
async def get_scraped_content(
    skip: int = 0,
    limit: int = 1,
    url: str = None,
    db: Session = Depends(get_db)
):
    query = db.query(ScrapedContent)
    if url:
        query = query.filter(ScrapedContent.url == url)
    content = query.order_by(ScrapedContent.created_at.desc()).offset(skip).limit(limit).all()
    return content

async def process_scraping_job(job_id: int, urls: List[str]):
    db = next(get_db())
    try:
        # Update job status
        job = db.query(ScrapingJob).filter(ScrapingJob.id == job_id).first()
        job.status = "running"
        db.commit()

        # Initialize scraper
        async with AsyncWebScraper() as scraper:
            results = await scraper.scrape_urls(urls)

            # Process results
            for result in results:
                if isinstance(result, Exception):
                    continue

                # Save to database
                content = ScrapedContent(
                    url=result['url'],
                    title=result['title'],
                    text=result['text'],
                    summary=result['summary'],
                    extra_metadata={'timestamp': result['timestamp']}
                )
                db.add(content)

            # Update job status
            job.status = "completed"
            job.results = results
            db.commit()

    except Exception as e:
        job.status = "failed"
        job.error = str(e)
        db.commit()
        raise 