from db import connect_db
import requests

def insert_or_update_pdf_data(company_name, file_name, source_url):
    try:
        conn = connect_db()
        cur = conn.cursor()

        cur.execute("""
            SELECT id FROM pdf_files 
            WHERE company_name = %s
        """, (company_name,))
        
        existing_record = cur.fetchone()

        if existing_record:
            cur.execute("""
                UPDATE pdf_files
                SET file_name = %s,
                    source_url = %s,
                    last_updated_at = CURRENT_TIMESTAMP
                WHERE company_name = %s
            """, (file_name, source_url, company_name))
            print(f"🔁 Updated PDF record for: {company_name}")
        else:
            cur.execute("""
                INSERT INTO pdf_files (file_name, company_name, source_url, last_updated_at)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            """, (file_name, company_name, source_url))
            print(f"✅ Inserted new PDF record for: {company_name}")

        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        print(f"DB Error: {e}")


def get_pdf_data(company_name):
    try:
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, file_name, company_name, source_url, last_updated_at
            FROM pdf_files 
            WHERE company_name = %s
        """, (company_name,))
        rows = cur.fetchall()
        cur.close()
        conn.close()

        return rows
    except Exception as e:
        print(f"DB Fetch Error: {e}")
        return []
    
def get_all_data_from_db():
    try:
        conn = connect_db()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, file_name, company_name, source_url, last_updated_at
            FROM pdf_files
        """)

        rows = cur.fetchall()

        cur.close()
        conn.close()

        if not rows:
            print("No data found.")
            return []

        for row in rows:
            print(f"ID: {row[0]}")
            print(f"File Name: {row[1]}")
            print(f"Company Name: {row[2]}")
            print(f"Source URL: {row[3]}")
            print(f"Last Updated: {row[4]}")
            print("-" * 60)

        return rows

    except Exception as e:
        print(f"DB Fetch All Error: {e}")
        return []