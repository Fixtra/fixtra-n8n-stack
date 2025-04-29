from flask import Flask, request, jsonify
import requests
import re
import logging
import time
import random
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import concurrent.futures
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import validators
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import os

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Financial keywords to identify relevant pages
FINANCIAL_KEYWORDS = [
    'financial', 'report', 'annual', 'investor', 'finance', 'earnings',
    'shareholder', 'sec', 'filing', 'statement', 'quarter', 'fiscal',
    'form 10-k', '10-k', 'form 10-q', '10-q', 'proxy', 'prospectus',
    'result', 'presentation', 'investor relation', 'annual report',
    'financial statement', 'balance sheet', 'income statement',
    'cash flow', 'sustainability', 'esg', 'corporate governance'
]

# Keywords that likely indicate financial PDF documents
PDF_KEYWORDS = [
    'annual report', 'financial report', 'annual financial report',
    'annual statement', 'financial statement', 'annual results',
    'financial results', 'interim report', 'quarterly report',
    'form 10-k', 'form 10-q', 'shareholder report', 'integrated report',
    'sustainability report', 'esg report', 'proxy statement',
    'year end', 'fiscal year', 'fy20', 'q1', 'q2', 'q3', 'q4'
]

# Common financial report sections in websites
FINANCIAL_SECTIONS = [
    'investor', 'investors', 'finance', 'financial', 'reports', 'ir',
    'investor-relations', 'investor_relations', 'investorrelations',
    'financials', 'financial-information', 'financial_information',
    'annual-reports', 'annual_reports', 'annualreports',
    'quarterly-reports', 'quarterly_reports', 'quarterlyreports',
    'sec-filings', 'sec_filings', 'secfilings',
    'financial-reports', 'financial_reports', 'financialreports',
    'financial-statements', 'financial_statements', 'financialstatements',
    'earnings', 'results', 'shareholders', 'reports-and-presentations',
    'publications', 'documents', 'downloads', 'resources'
]

# Anti-pattern URLs to avoid
AVOID_PATTERNS = [
    'javascript:', 'mailto:', 'tel:', 'whatsapp:', 'sms:', 'market-data',
    'stock-price', 'share-price', 'login', 'register', 'signin', 'signup',
    'sign-in', 'sign-up', 'account', 'password', 'careers', 'jobs', 'blog',
    'news', 'press', 'media', 'contact', 'about', 'faq', 'help', 'support',
    'terms', 'privacy', 'cookie', 'social', 'facebook', 'twitter', 'instagram',
    'linkedin', 'youtube', 'calendar', 'events', 'webcast', 'webinar',
    'search', 'site-map', 'sitemap', 'subscribe', 'chat', 'feedback',
    'products', 'services', 'solutions', 'portfolio', 'gallery', 'video',
    'audio', 'podcasts', 'forum', 'community', 'history', 'locations',
    'offices', 'facilities', 'sustainability', 'responsibility', 'leadership',
    'management', 'team', 'board', 'directors', 'governance', 'ethics',
    'compliance', 'policy', 'guidelines', 'program', 'initiative'
]

class FinancialReportScraper:
    def __init__(self):
        self.session = self._create_session()
        self.ua = UserAgent()
        self.visited_urls = set()
        self.financial_urls = []
        self.probable_pdf_urls = []
        self.confirmed_pdf_urls = []
        self.max_pages_to_scrape = 150  # Limit to avoid infinite crawling
        self.max_depth = 4  # Maximum depth for crawling
        self.delay_range = (0.5, 2.0)  # Random delay between requests
        self.semaphore = concurrent.futures.Semaphore(5)  # Limit concurrent requests
        self.use_browser = True  # Whether to use browser automation for dynamic content
        self.browser = None
        self.browser_wait_time = 5  # Seconds to wait for page loading
        
    def _create_session(self):
        """Create a requests session with retry strategy."""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "HEAD"],
            backoff_factor=1
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
        
    def _initialize_browser(self):
        """Initialize headless Chrome browser for handling dynamic content."""
        if self.browser is not None:
            return
            
        options = Options()
        options.add_argument("--headless")  # Run in headless mode
        options.add_argument("--no-sandbox")  # Required for Docker
        options.add_argument("--disable-dev-shm-usage")  # Required for Docker
        options.add_argument("--disable-gpu")
        options.add_argument(f"user-agent={self.ua.random}")
        options.add_argument("--window-size=1920,1080")
        
        # Add proxy settings if needed
        # if proxy:
        #     options.add_argument(f'--proxy-server={proxy}')
        
        # Check if running in Docker and use appropriate chromedriver path
        if os.path.exists("/usr/bin/chromedriver"):
            service = Service("/usr/bin/chromedriver")
        else:
            service = Service()
            
        try:
            self.browser = webdriver.Chrome(service=service, options=options)
            self.browser.set_page_load_timeout(30)  # Set page load timeout
        except Exception as e:
            logger.error(f"Failed to initialize browser: {str(e)}")
            self.use_browser = False
            
    def _close_browser(self):
        """Close the browser instance."""
        if self.browser:
            try:
                self.browser.quit()
            except Exception as e:
                logger.error(f"Error closing browser: {str(e)}")
            finally:
                self.browser = None
    
    def _get_random_headers(self):
        """Generate random headers for requests."""
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'TE': 'Trailers',
        }
    
    def _random_delay(self):
        """Introduce random delay between requests."""
        time.sleep(random.uniform(*self.delay_range))
    
    def _normalize_url(self, url, base_url):
        """Normalize URL by joining it with base URL if relative."""
        if not url:
            return None
        
        # Handle URLs that start with //
        if url.startswith('//'):
            parsed_base = urlparse(base_url)
            return f"{parsed_base.scheme}:{url}"
            
        # Join relative URLs with base URL
        if not url.startswith(('http://', 'https://')):
            return urljoin(base_url, url)
            
        return url
    
    def _is_valid_url(self, url, base_domain):
        """Check if URL is valid and belongs to the same domain."""
        if not url or not validators.url(url):
            return False
            
        # Skip URLs with unwanted patterns
        if any(pattern in url.lower() for pattern in AVOID_PATTERNS):
            return False
            
        # Check if URL is from the same domain or subdomain
        parsed_url = urlparse(url)
        parsed_base = urlparse(base_domain)
        
        # Get domain parts
        url_domain_parts = parsed_url.netloc.split('.')
        base_domain_parts = parsed_base.netloc.split('.')
        
        # Check if it's the same domain or subdomain
        if len(url_domain_parts) >= 2 and len(base_domain_parts) >= 2:
            url_main_domain = '.'.join(url_domain_parts[-2:])
            base_main_domain = '.'.join(base_domain_parts[-2:])
            return url_main_domain == base_main_domain
            
        return False
    
    def _is_financial_related(self, url, text=None):
        """Check if URL or text is related to financial reports."""
        if not url:
            return False
            
        url_lower = url.lower()
        
        # Check for PDF extension
        if url_lower.endswith('.pdf'):
            return True
            
        # Check for financial keywords in URL
        if any(keyword in url_lower for keyword in FINANCIAL_KEYWORDS):
            return True
            
        # Check for financial sections in URL
        if any(f"/{section}/" in url_lower or f"/{section}" == url_lower[-len(section)-1:] 
               for section in FINANCIAL_SECTIONS):
            return True
            
        # Check for financial keywords in link text
        if text:
            text_lower = text.lower()
            if any(keyword in text_lower for keyword in FINANCIAL_KEYWORDS):
                return True
                
        return False
    
    def _is_likely_financial_pdf(self, url, text=None):
        """Check if URL likely points to a financial PDF document."""
        if not url:
            return False
            
        url_lower = url.lower()
        
        # Check for PDF extension
        if not url_lower.endswith('.pdf'):
            return False
            
        # Check for financial PDF keywords in URL or text
        for keyword in PDF_KEYWORDS:
            if keyword in url_lower:
                return True
                
        if text:
            text_lower = text.lower()
            for keyword in PDF_KEYWORDS:
                if keyword in text_lower:
                    return True
                    
        return False
    
    def _get_base_domain(self, url):
        """Get base domain from URL."""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"
    
    def _get_page_content(self, url):
        """Get page content using either requests or browser depending on settings."""
        # Try with regular requests first
        try:
            with self.semaphore:
                self._random_delay()
                response = self.session.get(url, headers=self._get_random_headers(), timeout=10)
                
            if response.status_code != 200:
                logger.warning(f"Failed to fetch URL: {url}, Status code: {response.status_code}")
                return None, None
                
            content_type = response.headers.get('Content-Type', '').lower()
            if 'text/html' not in content_type:
                # If it's a PDF, check if it's financial related
                if 'application/pdf' in content_type:
                    return None, 'pdf'
                return None, None
                
            # If page has very little content, it might be JavaScript-driven
            if len(response.text) < 5000 and ('ng-app' in response.text or 'react' in response.text 
                  or 'vue' in response.text or '<script' in response.text):
                use_browser = True
            else:
                # Return the regular response for static pages
                return response.text, 'html'
                
        except Exception as e:
            logger.warning(f"Regular request failed for {url}: {str(e)}")
            use_browser = True
            
        # Fall back to browser for dynamic content if enabled
        if self.use_browser and use_browser:
            try:
                if not self.browser:
                    self._initialize_browser()
                
                if not self.browser:
                    logger.error("Browser initialization failed")
                    return None, None
                    
                self._random_delay()
                self.browser.get(url)
                
                # Wait for page to load
                WebDriverWait(self.browser, self.browser_wait_time).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Additional wait for dynamic content to load
                time.sleep(2)
                
                # Get rendered page content
                return self.browser.page_source, 'html'
                
            except (TimeoutException, WebDriverException) as e:
                logger.error(f"Browser automation error for {url}: {str(e)}")
                return None, None
                
        return None, None
            
    def _scrape_page(self, url, depth=0, base_domain=None):
        """Scrape a single page for financial report URLs."""
        if depth > self.max_depth or url in self.visited_urls or len(self.visited_urls) >= self.max_pages_to_scrape:
            return
            
        if not base_domain:
            base_domain = self._get_base_domain(url)
            
        self.visited_urls.add(url)
        
        try:
            page_content, content_type = self._get_page_content(url)
            
            if content_type == 'pdf':
                if self._is_financial_related(url):
                    self.confirmed_pdf_urls.append(url)
                return
                
            if not page_content:
                return
                
            soup = BeautifulSoup(page_content, 'html.parser')
            
            # Extract all links from the page
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                text = link.get_text(strip=True)
                
                # Normalize URL
                normalized_url = self._normalize_url(href, url)
                
                # Skip invalid URLs
                if not normalized_url or not self._is_valid_url(normalized_url, base_domain):
                    continue
                    
                # Check if link is likely a financial PDF
                if self._is_likely_financial_pdf(normalized_url, text):
                    self.probable_pdf_urls.append({
                        'url': normalized_url,
                        'text': text
                    })
                    
                # Check if link is related to financial reports
                if self._is_financial_related(normalized_url, text):
                    self.financial_urls.append({
                        'url': normalized_url,
                        'text': text
                    })
                    
                    # Recursively scrape financial-related pages
                    if depth < self.max_depth and normalized_url not in self.visited_urls:
                        self._scrape_page(normalized_url, depth + 1, base_domain)
                        
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
    
    def scrape_website(self, company_url, use_browser=True):
        """Scrape a company website for financial report URLs."""
        # Reset state
        self.visited_urls = set()
        self.financial_urls = []
        self.probable_pdf_urls = []
        self.confirmed_pdf_urls = []
        self.use_browser = use_browser
        
        if self.use_browser:
            self._initialize_browser()
        
        try:
            # Normalize company URL
            if not company_url.startswith(('http://', 'https://')):
                company_url = f"https://{company_url}"
                
            # Start with the home page
            self._scrape_page(company_url)
            
            # Look for investor relations or financial sections
            base_domain = self._get_base_domain(company_url)
            
            # Try to find investor relations or financial sections
            for section in FINANCIAL_SECTIONS:
                section_url = f"{base_domain}/{section}"
                if section_url not in self.visited_urls:
                    self._scrape_page(section_url, base_domain=base_domain)
                    
            # Check if we found any financial PDFs
            for url_info in self.financial_urls:
                url = url_info['url']
                text = url_info['text']
                
                # Check if it's a confirmed PDF
                if url.lower().endswith('.pdf'):
                    self.confirmed_pdf_urls.append(url)
                    continue
                    
                # Check if it's a potential PDF container
                if self._is_likely_financial_pdf(url, text):
                    self.probable_pdf_urls.append({
                        'url': url,
                        'text': text
                    })
                    
            # Verify probable PDFs
            verified_pdfs = []
            for pdf_info in self.probable_pdf_urls:
                pdf_url = pdf_info['url']
                if pdf_url not in self.confirmed_pdf_urls:
                    try:
                        with self.semaphore:
                            self._random_delay()
                            response = self.session.head(pdf_url, headers=self._get_random_headers(), timeout=5)
                            
                        content_type = response.headers.get('Content-Type', '').lower()
                        if 'application/pdf' in content_type:
                            verified_pdfs.append(pdf_url)
                            
                    except Exception as e:
                        logger.error(f"Error verifying PDF {pdf_url}: {str(e)}")
                        
            self.confirmed_pdf_urls.extend(verified_pdfs)
            
            # Extract unique results
            unique_financial_urls = []
            seen_urls = set()
            
            for url_info in self.financial_urls:
                url = url_info['url']
                if url not in seen_urls:
                    seen_urls.add(url)
                    unique_financial_urls.append(url_info)
                    
            return {
                'confirmed_pdf_urls': list(set(self.confirmed_pdf_urls)),
                'financial_urls': unique_financial_urls
            }
        finally:
            # Clean up browser resources
            if self.browser:
                self._close_browser()


@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Missing request data'}), 400
        
    if 'company_url' not in data:
        return jsonify({'error': 'Missing company_url parameter'}), 400
        
    company_url = data['company_url']
    
    # Optional parameters
    max_pages = data.get('max_pages', 150)
    max_depth = data.get('max_depth', 4)
    use_browser = data.get('use_browser', True)  # Whether to use browser automation
    
    try:
        scraper = FinancialReportScraper()
        scraper.max_pages_to_scrape = max_pages
        scraper.max_depth = max_depth
        
        result = scraper.scrape_website(company_url, use_browser=use_browser)
        
        # Format results
        financial_pages = []
        for item in result['financial_urls']:
            url = item['url']
            text = item.get('text', '')
            financial_pages.append({
                'url': url,
                'text': text,
                'is_pdf': url.lower().endswith('.pdf')
            })
        
        return jsonify({
            'company_url': company_url,
            'confirmed_pdf_urls': result['confirmed_pdf_urls'],
            'financial_pages': financial_pages,
            'metadata': {
                'total_pages_scraped': len(scraper.visited_urls),
                'total_financial_urls': len(result['financial_urls']),
                'total_confirmed_pdfs': len(result['confirmed_pdf_urls']),
                'used_browser_automation': use_browser
            }
        })
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)