from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import logging
import time
import os
import psutil
import sys
from search import search_financial_statement
from db import connect_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Financial Report Scraper")

class ScrapeRequest(BaseModel):
    company_url: str
    max_pages: int = 100
    max_depth: int = 3
    use_browser: bool = False

@app.post("/scrape")
async def scrape(request: ScrapeRequest):
    """
    Legacy endpoint that uses the improved search functionality internally.
    """
    company_url = request.company_url.strip()
    logger.info(f"Starting search for {company_url}")
    
    if not company_url:
        raise HTTPException(status_code=400, detail="Company URL is required.")
    
    # Extract company name from URL
    company_name = company_url.split("//")[-1].split(".")[0]
    if company_name.lower().startswith("www."):
        company_name = company_name[4:]
    
    # Use the improved search functionality
    try:
        results = search_financial_statement(company_name)
        
        if not results:
            # Return empty response in the same format as the original
            return {
                'company_url': company_url,
                'confirmed_pdf_urls': [],
                'financial_pages': [],
                'metadata': {
                    'total_pages_scraped': 0,
                    'total_financial_urls': 0,
                    'total_confirmed_pdfs': 0,
                    'used_browser_automation': False,
                    'status': 'success'
                }
            }
        
        # Format the response to match the original API
        pdf_url = results[0]
        return {
            'company_url': company_url,
            'confirmed_pdf_urls': [pdf_url],
            'financial_pages': [
                {
                    'url': pdf_url,
                    'text': f"{company_name} financial statement",
                    'is_pdf': True
                }
            ],
            'metadata': {
                'total_pages_scraped': 1,
                'total_financial_urls': 1,
                'total_confirmed_pdfs': 1,
                'used_browser_automation': False,
                'status': 'success'
            }
        }
    except Exception as e:
        logger.error(f"Error during search: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                'error': str(e),
                'company_url': company_url,
                'status': 'error',
                'message': 'Failed to search for financial statements'
            }
        )

@app.get("/health")
async def health():
    """Health check endpoint to verify the service is running."""
    # Basic health check information
    status = {
        'status': 'healthy',
        'time': time.time(),
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'service': 'financial-report-scraper',
        'memory_usage': {
            'active': 'unknown'
        }
    }

    # Try to get memory info if possible
    try:
        process = psutil.Process(os.getpid())
        status['memory_usage'] = {
            'active': round(process.memory_info().rss / 1024 / 1024, 2),  # MB
            'percent': round(process.memory_percent(), 2)
        }
    except Exception as e:
        status['memory_usage']['error'] = str(e)

    # Add system information
    status['system'] = {
        'python_version': sys.version,
        'platform': sys.platform
    }

    # Add database check
    try:
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        status['database'] = 'connected'
    except Exception as e:
        status['database'] = f'error: {str(e)}'

    return status

@app.post("/search_financial_statements")
async def search_financial_statements(request: Request):
    """
    New endpoint that directly uses the improved search functionality.
    """
    data = await request.json()
    company_name = data.get("company", "").strip()

    if not company_name:
        raise HTTPException(status_code=400, detail="Company name is required.")

    result = search_financial_statement(company_name)

    if result:
        return {"company": company_name, "pdf_url": result[0]}
    else:
        raise HTTPException(status_code=404, detail="No suitable PDF found.")

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=False)
