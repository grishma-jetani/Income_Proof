# IncomeProof
**Financial identity, simplified.**

IncomeProof is a full-stack web application designed to parse, verify, and analyze bank statements and UPI exports. It helps evaluate the income stability of gig-workers and freelancers by generating a robust, fraud-resistant "Income Stability Score."

##  What It Does

* **Smart Data Extraction:** Accurately reads transactions from Bank Statements PDFs and UPI exports.
* **Fraud Detection:** * Checks PDF metadata to flag manually created or edited files.
  * Audits row-by-row math to ensure debits/credits match the running balance (catching tampered numbers).
* **AI Categorization:** Uses a fast rule-based engine for common gig platforms (Swiggy, Zomato, Uber), and falls back to **Google Gemini AI** to smartly categorize unknown transactions.
* **5-Factor Stability Score:** Calculates a creditworthiness score based on income regularity, floor, trend momentum, platform concentration, and consistency.
* **Underwriter-Ready Reports:** Generates professional PDF reports detailing income trends, score breakdowns, and document authenticity warnings.

##  Tech Stack

* **Frontend:** React (Vite), Tailwind CSS
* **Backend:** Python, FastAPI
* **Database & Auth:** PostgreSQL, Supabase
* **PDF Processing:** `pdfplumber`, `reportlab`
* **AI:** Google Generative AI (Gemini)

##  Quick Start

### 1. Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
