# data/synthetic_generator/main.py
import os
from datetime import date

from generate_transactions import generate_transactions
from render_pdf_bank import render_bank_statement_pdf
from render_csv_upi import render_upi_csv
from render_pdf_phonepe import render_phonepe_pdf  # <-- Add this import

OUTPUT_DIR = os.path.join("..", "sample_statements")

if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # df = generate_transactions(start_date=date(2026, 1, 1), num_months=4, opening_balance=4500.0)

    # render_bank_statement_pdf(df, os.path.join(OUTPUT_DIR, "boi_statement_jan_apr_2026.pdf"))
    # render_upi_csv(df, os.path.join(OUTPUT_DIR, "phonepe_export_jan_apr_2026.csv"))
    
    # # <-- Add this line to generate the new PhonePe layout
    # render_phonepe_pdf(df, os.path.join(OUTPUT_DIR, "phonepe_statement_jan_apr_2026.pdf")) 
    df = generate_transactions(start_date=date(2026, 5, 2), num_months=3, opening_balance=4500.0)

    render_bank_statement_pdf(df, os.path.join(OUTPUT_DIR, "boi_statement_may_july_2026.pdf"))
    render_upi_csv(df, os.path.join(OUTPUT_DIR, "phonepe_export_may_july_2026.csv"))
    
    # <-- Add this line to generate the new PhonePe layout
    render_phonepe_pdf(df, os.path.join(OUTPUT_DIR, "phonepe_statement_may_july_2026.pdf"))

    df.to_csv(os.path.join(OUTPUT_DIR, "_ground_truth.csv"), index=False)

    print(f"Generated {len(df)} transactions.")
    print(f"Files written to: {os.path.abspath(OUTPUT_DIR)}")