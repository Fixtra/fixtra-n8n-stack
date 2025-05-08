import os
import requests
from db import connect_db

def save_file(file_name, file_data, save_path):
    os.makedirs(save_path, exist_ok=True)
    file_path = os.path.join(save_path, file_name)
    with open(file_path, "wb") as f:
        f.write(file_data)
    print(f"{file_name} saved at {file_path}")

def download_from_url(company_name):
    try:
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT file_name, source_url
            FROM pdf_files
            WHERE company_name = %s
        """, (company_name,))
        rows = cur.fetchall()

        if not rows:
            print(f"No PDF files found for company: {company_name}")
            return

        save_path = os.path.join(".", "reports", company_name)
        os.makedirs(save_path, exist_ok=True)

        for file_name, source_url in rows:
            source_url = source_url.strip()
            print(f"Downloading from: {source_url}")
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                }
                response = requests.get(source_url, headers=headers, timeout=20)
                response.raise_for_status()
                save_file(file_name, response.content, save_path)
                print(f"Saved: {os.path.join(save_path, file_name)}")
            except requests.exceptions.RequestException as e:
                print(f"Failed to download {file_name} from {source_url}: {e}")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"URL Download Error: {e}")
