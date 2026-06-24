# data/synthetic_generator/tamper_boi_statement.py
import os
import pandas as pd
from render_pdf_bank import render_bank_statement_pdf

GROUND_TRUTH = os.path.join("..", "sample_statements", "_ground_truth.csv")
OUTPUT_DIR = os.path.join("..", "sample_statements")

if __name__ == "__main__":
    # Load the ground truth data
    df = pd.read_csv(GROUND_TRUTH, parse_dates=["date"])

    # Pick a 'credit' (Deposit) transaction roughly in the middle of the statement
    credit_rows = df[df["credit"] > 0].index
    target_idx = credit_rows[len(credit_rows) // 2]

    # --- THE TAMPER ---
    original_amount = df.loc[target_idx, "credit"]
    
    # We inflate the deposit by Rs. 8,500 to look like extra gig income
    df.loc[target_idx, "credit"] = original_amount + 8500.00 
    
    # Crucially, we DO NOT update the 'balance' column for this row or any subsequent rows.
    # This simulates a user editing the text of a deposit amount on the PDF, 
    # but failing to recalculate the running balance for the rest of the document.

    # Render it using your updated BOI generator
    output_path = os.path.join(OUTPUT_DIR, "boi_statement_TAMPERED.pdf")
    render_bank_statement_pdf(df, output_path)

    print(f"Tampered row {target_idx}: 'Deposit' changed from {original_amount} to {df.loc[target_idx, 'credit']}")
    print(f"File written to: {os.path.abspath(output_path)}")
    print("The printed balance is now mathematically incorrect from this row onward.")