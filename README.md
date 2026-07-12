# IncomeProof
**Financial identity, simplified.**

IncomeProof is a full-stack web application designed to parse, verify, and analyze bank statements and UPI exports. It helps evaluate the income stability of gig-workers and freelancers by generating a robust, fraud-resistant "Income Stability Score."

##  What It Does

- **Smart Data Extraction:** Accurately reads transactions from Bank Statement PDFs and UPI exports.
- **Fraud Detection:** 
  - Checks PDF metadata to flag manually created or edited files.
  - Audits row-by-row math to ensure debits/credits match the running balance (catching tampered numbers).
- **AI Categorization:** Uses a fast rule-based engine for common gig platforms (Swiggy, Zomato, Uber), and falls back to **Google Gemini AI** to smartly categorize unknown transactions.
- **5-Factor Stability Score:** Calculates a creditworthiness score based on income regularity, floor, trend momentum, platform concentration, and consistency.
- **Asynchronous Processing:** Handles 10MB+ documents in the background with **automatic retries** (3 attempts, exponential backoff) for fault tolerance.
- **Underwriter-Ready Reports:** Generates professional PDF reports detailing income trends, score breakdowns, and document authenticity warnings.

##  Tech Stack

- **Frontend:** React (Vite), Tailwind CSS
- **Backend:** Python, FastAPI
- **Task Queue:** Celery (with automatic retry & exponential backoff)
- **Message Broker:** Redis
- **Database & Auth:** PostgreSQL, Supabase
- **PDF Processing:** `pdfplumber`, `reportlab`
- **AI:** Google Generative AI (Gemini)

##  Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- Redis (installed and running locally)

### 1. Clone the Repository
```bash
git clone https://github.com/grishma-jetani/Income_Proof.git
cd Income_Proof
```

### 1. Backend Environment & Services
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
Update .env file in the backend directory and add your credentials:

```env
DATABASE_URL=your_database_url_here
GEMINI_API_KEY=your_gemini_api_key_here
UPLOAD_DIR=uploads
SUPABASE_URL=https://[YOUR_PROJECT].supabase.co
REDIS_URL=redis://localhost:6379/0
```

Start Redis On Linux (WSL/Ubuntu):
```bash
sudo service redis-server start
```

### 3. Start the Celery Worker
Open a second terminal, activate the virtual environment, and boot the background worker:
```bash
cd backend
source venv/bin/activate
celery -A app.core.celery_app worker --loglevel=info
```

### 4. Start the FastAPI server:
```bash
uvicorn app.main:app --reload
```

### 5. Frontend Setup
```bash
cd frontend
npm install
```
Update .env file in the frontend root directory

```env
VITE_SUPABASE_URL=https://[YOUR_PROJECT].supabase.co
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key_here
VITE_API_URL=http://localhost:8000
```

Start the frontend:
```bash
npm run dev
```
### 6. Access the Application

Open your browser and navigate to: http://localhost:5173
