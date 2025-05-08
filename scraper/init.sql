CREATE TABLE IF NOT EXISTS pdf_files (
    id SERIAL PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    source_url TEXT NOT NULL,
    last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_company_name ON pdf_files(company_name);