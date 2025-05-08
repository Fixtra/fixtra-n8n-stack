# Financial Report Scraper

A containerized service for finding and retrieving financial statements from company websites through an API.

## Overview

This service provides a REST API for searching financial statements (annual reports, 10-K filings, etc.) for public companies. It uses SerpAPI to perform intelligent searches and returns PDF links that can be used for automated data extraction workflows.

## Architecture

- **FastAPI Application**: Modern, high-performance web framework
- **PostgreSQL Database**: Persists search results and financial document URLs
- **SerpAPI Integration**: Performs targeted searches for financial documents
- **Docker Containers**: Ensures consistent deployment and isolation

## Installation & Setup

### Prerequisites

- Docker and Docker Compose
- SerpAPI key (get one at [serpapi.com](https://serpapi.com/))

### Configuration

1. Add your SerpAPI key to the `.env` file in the root directory:

```
# Existing n8n variables
...

# Scraper configuration
SERPAPI_API_KEY=your_serpapi_key_here
```

### Deployment

Use the provided rebuild script to deploy or update the scraper:

```bash
./rebuild-scraper.sh
```

This will:
1. Stop existing scraper containers
2. Build a new image with the latest code
3. Start the scraper and its PostgreSQL container
4. Connect them to the n8n network

### Verifying Installation

Check if the service is running:

```bash
docker ps | grep n8n-scraper
curl http://localhost:5000/health
```

## API Endpoints

### 1. Search Financial Statements

**Endpoint:** `POST /search_financial_statements`

**Request:**
```json
{
  "company": "Apple"
}
```

**Response:**
```json
{
  "company": "Apple",
  "pdf_url": "https://investor.apple.com/docs/FY23_10-K_Final_Filed.pdf"
}
```

### 2. Legacy Scrape Endpoint (Compatible with existing n8n workflows)

**Endpoint:** `POST /scrape`

**Request:**
```json
{
  "company_url": "apple.com",
  "max_pages": 100,
  "max_depth": 3,
  "use_browser": false
}
```

**Response:**
```json
{
  "company_url": "apple.com",
  "confirmed_pdf_urls": ["https://investor.apple.com/docs/FY23_10-K_Final_Filed.pdf"],
  "financial_pages": [
    {
      "url": "https://investor.apple.com/docs/FY23_10-K_Final_Filed.pdf",
      "text": "apple financial statement",
      "is_pdf": true
    }
  ],
  "metadata": {
    "total_pages_scraped": 1,
    "total_financial_urls": 1,
    "total_confirmed_pdfs": 1,
    "used_browser_automation": false,
    "status": "success"
  }
}
```

### 3. Health Check

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "time": 1683568762.6795828,
  "timestamp": "2025-05-08 14:32:42",
  "service": "financial-report-scraper",
  "memory_usage": {
    "active": 48.32,
    "percent": 0.59
  },
  "system": {
    "python_version": "3.11.5 (main, Aug 24 2023, 06:23:23) [GCC 12.2.0]",
    "platform": "linux"
  },
  "database": "connected"
}
```

## Using with n8n

To call the scraper API from n8n workflows:

1. Add an HTTP Request node
2. Set the method to "POST"
3. Set the URL to `http://n8n-scraper:5000/search_financial_statements`
   - Note: Use the container name (`n8n-scraper`) not `localhost`
4. Set the body to JSON and include the company name:
   ```json
   {
     "company": "{{$node["Previous_Node"].json.companyName}}"
   }
   ```
5. Process the response which will contain the PDF URL

## Configuration Options

The scraper can be configured through environment variables in the `scraper-compose.yml` file:

```yaml
environment:
  - DB_NAME=financial_files
  - DB_USER=postgres
  - DB_PASSWORD=scraper_secret_password
  - DB_HOST=scraper-postgres
  - SERPAPI_API_KEY=${SERPAPI_API_KEY}
```

## Troubleshooting

### Cannot Connect from n8n

If you receive connection refused errors in n8n when trying to connect to the scraper:

1. Make sure you're using the container name in the URL (`http://n8n-scraper:5000/...`)
2. Check if both containers are on the same network:
   ```bash
   docker inspect n8n-main | grep -A 20 Networks
   docker inspect n8n-scraper | grep -A 20 Networks
   ```
3. Check if the scraper container is running:
   ```bash
   docker ps | grep n8n-scraper
   ```
4. Check the scraper logs:
   ```bash
   docker logs n8n-scraper
   ```

### Database Issues

If you encounter PostgreSQL connection issues:

1. Check the database container is running:
   ```bash
   docker ps | grep n8n-scraper-postgres
   ```
2. Check if database initialization completed:
   ```bash
   docker logs n8n-scraper-postgres
   ```

## Development

### Container Structure

- `n8n-scraper`: FastAPI application container
- `n8n-scraper-postgres`: PostgreSQL database container

### Important Files

- `app.py`: Main FastAPI application
- `search.py`: SerpAPI search implementation
- `models.py`: Database models and operations
- `db.py`: Database connection handling
- `startup.sh`: Container initialization script
- `init.sql`: Database schema

### Volumes

- `scraper_data`: Stores downloaded PDFs
- `scraper_postgres_data`: Persists PostgreSQL data

### Rebuilding After Code Changes

After making changes to the code, rebuild the container:

```bash
./rebuild-scraper.sh
```

## API Rate Limits

Be aware of SerpAPI rate limits based on your plan. The default implementation includes retries and error handling for API rate limit issues, but excessive queries could exhaust your quota.