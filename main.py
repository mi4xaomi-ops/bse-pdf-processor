from fastapi import FastAPI
import fitz  # PyMuPDF
import pdfplumber
import requests
import re
import io

app = FastAPI()

@app.post("/process-pdf")
async def process_pdf(data: dict):

    pdf_url = data.get("pdf_url")

    if not pdf_url:
        return {"error": "No PDF URL provided"}

    response = requests.get(pdf_url)
    pdf_bytes = io.BytesIO(response.content)

    # -------- TEXT EXTRACTION (PyMuPDF) ----------
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    full_text = ""

    for page in doc:
        full_text += page.get_text()

    doc.close()

    # -------- TABLE EXTRACTION (pdfplumber) ----------
    tables_data = []

    with pdfplumber.open(pdf_bytes) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                tables_data.append(table)

    # -------- SIMPLE FINANCIAL METRIC EXTRACTION ----------
    revenue_match = re.search(r"Revenue.*?([\d,]+)", full_text, re.IGNORECASE)
    profit_match = re.search(r"Profit.*?([\d,]+)", full_text, re.IGNORECASE)

    structured_data = {
        "summary": full_text[:800],
        "revenue": revenue_match.group(1) if revenue_match else None,
        "profit": profit_match.group(1) if profit_match else None,
        "tables_found": len(tables_data),
        "raw_tables": tables_data[:2]
    }

    return structured_data