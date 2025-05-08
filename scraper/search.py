from serpapi import GoogleSearch
from config import SERPAPI_API_KEY
from models import insert_or_update_pdf_data
import json
import urllib.parse

def save_results_to_json(company_name, search_results, filename="results.json"):
    data = {
        company_name: search_results
    }

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def search_financial_statement(company_name):
    print(f"🔍 Searching for: {company_name}")

    query = f"{company_name} financial statement 2024 filetype:pdf"
    params = {
        "engine": "google",
        "q": query,
        "api_key": SERPAPI_API_KEY
    }

    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        print("✅ API response received")
    except Exception as e:
        print(f"🚨 Error fetching from SerpAPI: {e}")
        return None

    organic_results = results.get("organic_results", [])
    print(f"📊 Total results fetched: {len(organic_results)}")

    include_keywords = ["financial statement", "financial results", "annual", "report", "earnings"]
    exclude_keywords = ["q1", "q2", "q3", "q4", "1h", "h1", "half-year", "interim", "quarter"]

    def is_relevant_pdf(result):
        link = result.get("link", "")
        parsed_url = urllib.parse.urlparse(link)
        if ".pdf" not in parsed_url.path:
            return False

        title = result.get("title", "").lower()
        snippet = result.get("snippet", "").lower()

        contains_included = any(kw in title or kw in snippet for kw in include_keywords)
        contains_excluded = any(kw in title or kw in snippet for kw in exclude_keywords)

        return contains_included and not contains_excluded

    pdf_link_found = None
    for result in organic_results:
        if is_relevant_pdf(result):
            pdf_link_found = result.get("link")
            print(f"📄 Found relevant PDF: {pdf_link_found}")
            break

    if pdf_link_found:
        file_name = pdf_link_found.split("/")[-1].split("?")[0]
        insert_or_update_pdf_data(company_name, file_name, pdf_link_found)
    else:
        print("❗ No suitable PDF found.")

    save_results_to_json(company_name, organic_results)
    return [pdf_link_found] if pdf_link_found else None
