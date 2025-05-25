from typing import List, Optional, Dict, Any
import asyncio
from datetime import datetime
import aiohttp
from bs4 import BeautifulSoup
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_openai import ChatOpenAI
from langchain.chains.summarize import load_summarize_chain
import json

class AsyncWebScraper:
    def __init__(
        self,
        rate_limit: int = 5,
        timeout: int = 10,
        max_retries: int = 2
    ):
        self.rate_limit = rate_limit
        self.timeout = timeout
        self.max_retries = max_retries
        self.semaphore = asyncio.Semaphore(rate_limit)
        self.session: Optional[aiohttp.ClientSession] = None
        self.llm = ChatOpenAI(
            temperature=0,
            model_name="gpt-3.5-turbo"
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=4000,
            chunk_overlap=0
        )

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def fetch_page(self, url: str) -> str:
        """Fetch a single page with rate limiting and retries."""
        for attempt in range(self.max_retries):
            try:
                async with self.semaphore:
                    async with self.session.get(url, timeout=self.timeout) as response:
                        response.raise_for_status()
                        return await response.text()
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(1)

    def extract_content(self, soup: BeautifulSoup) -> str:
        """Extract content from the page using an improved approach."""
        # Remove unwanted elements
        for element in soup.find_all(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe', 'noscript', 'meta', 'link']):
            element.decompose()

        # Find the main content area
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=['content', 'main', 'article'])
        
        if main_content:
            # If we found a main content area, use that
            content_area = main_content
        else:
            # Otherwise use the body
            content_area = soup.body or soup

        # Get all text elements in order
        elements = content_area.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote'])
        
        # Extract text and join with proper spacing
        results_text = []
        for element in elements:
            text = element.get_text(separator=' ', strip=True)
            if text:  # Only add non-empty text
                results_text.append(text)
        
        # Join with double newlines to preserve structure
        content = '\n\n'.join(results_text)
        
        # Clean up extra whitespace
        content = ' '.join(content.split())
        
        return content

    async def generate_summary(self, text: str) -> str:
        """Generate a summary using LangChain and OpenAI."""
        # Split text into smaller chunks
        docs = [Document(page_content=text)]
        split_docs = self.text_splitter.split_documents(docs)
        
        # Use a simpler chain type for faster processing
        chain = load_summarize_chain(
            self.llm,
            chain_type="stuff",
            verbose=False
        )
        
        # Generate summary
        summary = await chain.arun(split_docs)
        return summary

    def create_error_result(self, url: str, error: Exception) -> Dict[str, Any]:
        """Create a properly formatted error result."""
        return {
            'url': url,
            'error': str(error),
            'timestamp': datetime.utcnow().isoformat(),
            'title': '',
            'text': '',
            'summary': f"Error generating summary: {str(error)}"
        }

    async def scrape_url(self, url: str) -> dict:
        """Scrape a single URL and process its content."""
        try:
            html = await self.fetch_page(url)
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract content
            text = self.extract_content(soup)
            
            # Generate AI summary
            summary = await self.generate_summary(text)
            
            content = {
                'url': url,
                'timestamp': datetime.utcnow().isoformat(),
                'title': soup.title.string if soup.title else '',
                'text': text,
                'summary': summary
            }
            
            # Ensure all content is JSON serializable
            return json.loads(json.dumps(content))
        except Exception as e:
            return self.create_error_result(url, e)

    async def scrape_urls(self, urls: List[str]) -> List[dict]:
        """Scrape multiple URLs concurrently."""
        # If only one URL is provided, use scrape_url directly
        if len(urls) == 1:
            result = await self.scrape_url(urls[0])
            return [result]
            
        # For multiple URLs, use concurrent scraping
        tasks = [self.scrape_url(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and ensure proper error handling
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(self.create_error_result(urls[i], result))
            else:
                processed_results.append(result)
        
        return processed_results 
        