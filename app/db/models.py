from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class ScrapedContent(Base):
    __tablename__ = "scraped_content"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(2048), unique=True, index=True)
    title = Column(String(512))
    text = Column(Text)
    summary = Column(Text)
    extra_metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ScrapingJob(Base):
    __tablename__ = "scraping_jobs"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String(50))  # pending, running, completed, failed
    urls = Column(ARRAY(String))  # List of URLs to scrape
    results = Column(JSON)  # Results of scraping
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 