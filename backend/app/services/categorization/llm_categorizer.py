import json
import logging
import re

import google.generativeai as genai

from app.core.config import settings
from app.services.categorization.rules import PLATFORM_PAYOUT_CATEGORIES

logger = logging.getLogger(__name__)

CATEGORIES = sorted(PLATFORM_PAYOUT_CATEGORIES) + [
    "Salary",
    "Rent",
    "Groceries & Food",
    "Utilities & EMI",
    "Loan EMI",
    "Transfers to Family",
    "Cash Withdrawal",
    "Personal / Other",
]

SYSTEM_PROMPT = f"""You are a financial transaction categorizer for an Indian gig-worker income app.

Categorize each transaction description into EXACTLY one of these categories:
{", ".join(CATEGORIES)}

Rules:
- Use the specific platform name (e.g. "Swiggy Payout", "Uber Earnings") when the platform is identifiable
- Salary = fixed salary from a traditional employer (not gig platforms)
- Rent = rent or accommodation payments
- Groceries & Food = supermarkets, grocery stores, restaurants, food delivery orders
- Utilities & EMI = phone recharge, electricity, water, gas, internet bills
- Loan EMI = loan repayments, EMIs, NACH debits
- Transfers to Family = money sent to family members
- Cash Withdrawal = ATM withdrawals
- Personal / Other = everything else that does not fit above

Return ONLY a valid JSON object. No explanation, no markdown, no code fences.
Format: {{"description1": "Category", "description2": "Category"}}"""


def _configure_gemini():
    if not settings.GEMINI_API_KEY:
        return None
    genai.configure(api_key=settings.GEMINI_API_KEY)
    return genai.GenerativeModel("gemini-2.5-flash")


def categorize_with_llm(uncategorized: list[dict]) -> dict[str, str]:
    if not uncategorized:
        return {}

    unique_descriptions = list({t["description"] for t in uncategorized})
    fallback = {d: "Personal / Other" for d in unique_descriptions}

    model = _configure_gemini()
    if model is None:
        logger.warning("GEMINI_API_KEY not set — all uncategorized → 'Personal / Other'")
        return fallback

    desc_list = "\n".join(f'"{d}"' for d in unique_descriptions)
    prompt = f"{SYSTEM_PROMPT}\n\nDescriptions to categorize:\n{desc_list}"

    try:
        response = model.generate_content(prompt)
        raw = response.text.strip()
        raw = re.sub(r"^```(?:json)?", "", raw).rstrip("`").strip()
        mapping = json.loads(raw)

        validated = {}
        for desc, cat in mapping.items():
            validated[desc] = cat if cat in CATEGORIES else "Personal / Other"
        for d in unique_descriptions:
            if d not in validated:
                validated[d] = "Personal / Other"
        return validated

    except Exception as exc:
        logger.error("Gemini categorization failed: %s", exc)
        return fallback


def apply_llm_categories(transactions: list[dict], mapping: dict[str, str]) -> list[dict]:
    result = []
    for txn in transactions:
        if txn.get("category") is None:
            txn = {**txn, "category": mapping.get(txn["description"], "Personal / Other")}
        result.append(txn)
    return result