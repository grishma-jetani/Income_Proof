"""
IncomeProof — Multi-Factor Income Stability Score
──────────────────────────────────────────────────
Five-factor weighted composite model for irregular gig-worker income.

Factor methodology:

1. Regularity Index (30%)
   Uses Median Absolute Deviation (MAD) instead of standard deviation
   for robustness against outliers, following Farrell & Greig (2016).
   Robust CV = MAD / median (where MAD = median(|Xi - median(X)|))
   Score = 100 * exp(-2.5 * robust_CV)
   — exponential decay penalises high variance non-linearly,
     matching how lenders perceive income risk.

2. Income Floor Ratio (25%)
   P10 income / median income, inspired by US Financial Diaries
   P10-to-median ratio methodology (Morduch & Schneider, 2017).
   Captures "how bad is the worst period" rather than average volatility.
   Score = min((P10 / median) * 125, 100)
   — A floor of 80% median = very strong. A floor of 0 = worst case.

3. Trend Momentum (20%)
   Linear regression slope weighted by R² (goodness of fit).
   A rising trend with low R² (noisy) is worth less than a rising
   trend with high R² (consistent). Prevents rewarding random
   upward noise as "strong positive trend."
   Score = 50 + (normalised_slope * R²) * 50

4. Platform Diversification (15%)
   Inverted Herfindahl-Hirschman Index (HHI).
   HHI = Σ(share_i²), ranges from 1/n (perfect diversity) to 1 (monopoly).
   Score = (1 - HHI) * 100
   — 1 platform: HHI=1, Score=0
   — 2 equal platforms: HHI=0.5, Score=50
   — 4 equal platforms: HHI=0.25, Score=75

5. Persistence Score (10%)
   Lag-1 autocorrelation of weekly income.
   Positive autocorrelation (good weeks follow good weeks) means
   income is predictable and lenders can rely on forward earnings.
   Score = (autocorrelation + 1) / 2 * 100
   — Normalises [-1, +1] to [0, 100].
"""

from datetime import date

import numpy as np
import pandas as pd
from scipy import stats

from app.services.categorization.rules import INCOME_CATEGORIES, PLATFORM_PAYOUT_CATEGORIES


# ── Factor weights — must sum to 1.0 ──────────────────────────────────────
WEIGHTS = {
    "regularity": 0.30,
    "income_floor": 0.25,
    "trend_momentum": 0.20,
    "diversification": 0.15,
    "persistence": 0.10,
}

# Minimum weeks of data required for each factor to be meaningful
MIN_WEEKS_REGULARITY = 4
MIN_WEEKS_TREND = 6
MIN_WEEKS_PERSISTENCE = 8


# ══════════════════════════════════════════════════════════════════════════ #
#  Individual factor calculators                                            #
# ══════════════════════════════════════════════════════════════════════════ #

def _factor_regularity(weekly: pd.Series) -> tuple[float, dict]:
    """
    Robust CV using Median Absolute Deviation.
    Returns (score_0_to_100, metadata_dict)
    """
    if len(weekly) < MIN_WEEKS_REGULARITY or weekly.median() == 0:
        return 50.0, {"method": "insufficient_data", "robust_cv": None}

    median_income = weekly.median()
    mad = (weekly - median_income).abs().median()
    robust_cv = mad / median_income   # analogous to CV but outlier-resistant

    # Exponential decay: score = 100 * e^(-2.5 * CV)
    # CV=0.00 → 100, CV=0.20 → 61, CV=0.40 → 37, CV=0.60 → 22, CV=1.00 → 8
    score = 100.0 * np.exp(-2.5 * robust_cv)

    return round(float(score), 2), {
        "method": "mad_robust_cv",
        "median_weekly_income": round(float(median_income), 2),
        "mad": round(float(mad), 2),
        "robust_cv": round(float(robust_cv), 4),
        "interpretation": _cv_interpretation(robust_cv),
    }


def _cv_interpretation(cv: float) -> str:
    if cv < 0.15:
        return "Very consistent — income varies less than 15% week to week (robust measure)"
    if cv < 0.30:
        return "Moderately consistent — typical for active gig workers"
    if cv < 0.50:
        return "Variable — significant week-to-week swings"
    return "Highly volatile — income is difficult to predict"


def _factor_income_floor(weekly: pd.Series) -> tuple[float, dict]:
    """
    P10/median ratio — how bad is the worst-decile week vs the median.
    Inspired by US Financial Diaries P10-to-median methodology.
    """
    if len(weekly) < MIN_WEEKS_REGULARITY or weekly.median() == 0:
        return 50.0, {"method": "insufficient_data", "p10": None, "p10_to_median_ratio": None}

    p10 = float(weekly.quantile(0.10))
    median = float(weekly.median())
    p25 = float(weekly.quantile(0.25))

    ratio = p10 / median   # 0 = worst possible, 1 = perfectly flat income

    # Scale: ratio of 0.8+ → 100, ratio of 0 → 0
    # Multiply by 125 so ratio=0.8 maps to 100 (cap at 100)
    score = min(ratio * 125, 100.0)
    score = max(score, 0.0)

    return round(score, 2), {
        "method": "p10_to_median",
        "p10_weekly": round(p10, 2),
        "p25_weekly": round(p25, 2),
        "median_weekly": round(median, 2),
        "p10_to_median_ratio": round(ratio, 4),
        "interpretation": _floor_interpretation(ratio),
    }


def _floor_interpretation(ratio: float) -> str:
    if ratio >= 0.70:
        return "Strong income floor — worst weeks are still 70%+ of typical income"
    if ratio >= 0.40:
        return "Moderate floor — some very low weeks but not catastrophic"
    if ratio >= 0.20:
        return "Weak floor — occasional near-zero income weeks"
    return "Very low floor — some weeks had minimal or no income"


def _factor_trend_momentum(weekly: pd.Series) -> tuple[float, dict]:
    """
    OLS slope weighted by R² (coefficient of determination).
    Rewards consistent upward trends; discounts noisy upward noise.
    """
    if len(weekly) < MIN_WEEKS_TREND:
        return 50.0, {"method": "insufficient_data", "slope": None, "r_squared": None}

    x = np.arange(len(weekly))
    y = weekly.values

    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    r_squared = r_value ** 2
    mean_income = float(weekly.mean())

    # Normalise slope as % of mean income per week
    slope_pct = slope / mean_income if mean_income > 0 else 0.0

    # Weight slope by R² — a noisy trend is discounted
    weighted_slope = slope_pct * r_squared

    # Map to 0-100:
    # weighted_slope of +0.05 (5% growth/week with perfect R²) → ~100
    # weighted_slope of 0 → 50
    # weighted_slope of -0.05 → ~0
    score = 50.0 + (weighted_slope * 50.0 / 0.05)
    score = max(min(score, 100.0), 0.0)

    trend_direction = "upward" if slope > 0 else "downward" if slope < 0 else "flat"
    significance = "statistically significant (p<0.05)" if p_value < 0.05 else "not statistically significant"

    return round(score, 2), {
        "method": "ols_r2_weighted",
        "slope_per_week": round(float(slope), 2),
        "slope_pct_per_week": round(float(slope_pct), 4),
        "r_squared": round(float(r_squared), 4),
        "p_value": round(float(p_value), 4),
        "weighted_slope": round(float(weighted_slope), 6),
        "trend_direction": trend_direction,
        "significance": significance,
        "interpretation": f"{trend_direction.capitalize()} trend ({significance}), R²={r_squared:.2f}",
    }


def _factor_diversification(income_txns: list[dict]) -> tuple[float, dict]:
    """
    Inverted Herfindahl-Hirschman Index across platform income sources.
    Standard industrial-organisation concentration measure.
    """
    platform_totals: dict[str, float] = {}
    for t in income_txns:
        cat = t.get("category", "Other")
        if cat in PLATFORM_PAYOUT_CATEGORIES or cat == "Salary":
            platform_totals[cat] = platform_totals.get(cat, 0) + float(t.get("credit", 0))

    if not platform_totals:
        return 50.0, {"method": "no_platform_data", "hhi": None, "platform_count": 0}

    total = sum(platform_totals.values())
    if total == 0:
        return 50.0, {"method": "zero_income", "hhi": None}

    # HHI = Σ(market_share_i²)
    shares = {p: v / total for p, v in platform_totals.items()}
    hhi = sum(s ** 2 for s in shares.values())

    # Inverted and scaled: HHI=1 (monopoly) → 0, HHI=0.25 → 75, HHI=0 → 100
    score = (1.0 - hhi) * 100.0

    return round(score, 2), {
        "method": "inverted_hhi",
        "platform_count": len(platform_totals),
        "platform_shares": {p: round(s, 4) for p, s in shares.items()},
        "hhi": round(hhi, 4),
        "interpretation": _hhi_interpretation(hhi, len(platform_totals)),
    }


def _hhi_interpretation(hhi: float, n_platforms: int) -> str:
    if n_platforms == 1:
        return "Single platform — full concentration risk. Income disappears if this platform reduces rates or availability"
    if hhi > 0.60:
        return f"High concentration across {n_platforms} platforms — one platform dominates earnings"
    if hhi > 0.35:
        return f"Moderate concentration across {n_platforms} platforms"
    return f"Well-diversified across {n_platforms} platforms — strong resilience to platform-specific shocks"


def _factor_persistence(weekly: pd.Series) -> tuple[float, dict]:
    """
    Lag-1 autocorrelation of weekly income.
    Positive autocorrelation = good weeks predict future good weeks.
    This is the 'predictability' dimension lenders rely on for forward-looking
    income estimates.
    """
    if len(weekly) < MIN_WEEKS_PERSISTENCE:
        return 50.0, {"method": "insufficient_data", "lag1_autocorrelation": None}

    # pandas autocorr uses Pearson correlation with lag
    lag1 = float(weekly.autocorr(lag=1))

    if np.isnan(lag1):
        return 50.0, {"method": "autocorr_nan", "lag1_autocorrelation": None}

    # Normalise from [-1, 1] to [0, 100]
    score = (lag1 + 1.0) / 2.0 * 100.0

    return round(score, 2), {
        "method": "lag1_pearson_autocorrelation",
        "lag1_autocorrelation": round(lag1, 4),
        "interpretation": _autocorr_interpretation(lag1),
    }


def _autocorr_interpretation(ac: float) -> str:
    if ac > 0.40:
        return "Strong positive persistence — high-earning weeks are reliably followed by more high-earning weeks"
    if ac > 0.15:
        return "Moderate persistence — some predictability in week-to-week income"
    if ac > -0.15:
        return "Near-random week-to-week variation — income does not follow a predictable short-term pattern"
    return "Negative persistence — high weeks tend to be followed by low weeks (boom-bust cycle)"


# ══════════════════════════════════════════════════════════════════════════ #
#  Composite score + explanation                                            #
# ══════════════════════════════════════════════════════════════════════════ #

def _composite_score(factor_scores: dict[str, float]) -> float:
    """
    Weighted average. Weights defined in WEIGHTS constant at top of file.
    """
    total = sum(
        factor_scores[name] * weight
        for name, weight in WEIGHTS.items()
    )
    return round(max(min(total, 100.0), 0.0), 2)


def _score_band(score: float) -> str:
    if score >= 78:
        return "Prime"
    if score >= 62:
        return "Standard"
    if score >= 45:
        return "Developing"
    return "Limited"


def _build_explanation(
    score: float,
    factor_scores: dict[str, float],
    factor_meta: dict[str, dict],
    num_weeks: int,
) -> str:
    band = _score_band(score)
    reg_meta = factor_meta.get("regularity", {})
    floor_meta = factor_meta.get("income_floor", {})
    trend_meta = factor_meta.get("trend_momentum", {})
    div_meta = factor_meta.get("diversification", {})

    median_income = reg_meta.get("median_weekly_income", 0)
    p10 = floor_meta.get("p10_weekly", 0)
    trend_dir = trend_meta.get("trend_direction", "flat")
    n_platforms = div_meta.get("platform_count", 1)

    # Identify the weakest factor for targeted advice
    weakest_factor = min(factor_scores, key=lambda k: factor_scores[k])
    weakest_score = factor_scores[weakest_factor]

    explanation = (
        f"Over {num_weeks} weeks, your median weekly gig income was "
        f"₹{median_income:,.0f}, with a minimum-decile floor of ₹{p10:,.0f} "
        f"(your worst 10% of weeks). "
        f"Earnings show a {trend_dir} trend, drawn from "
        f"{'a single platform' if n_platforms == 1 else f'{n_platforms} platforms'}. "
        f"Your composite stability score is {score:.0f}/100 — {band} tier."
    )

    return explanation


def _build_action_tip(
    score: float,
    factor_scores: dict[str, float],
    factor_meta: dict[str, dict],
) -> str:
    band = _score_band(score)

    # Find two weakest factors and give targeted advice
    sorted_factors = sorted(factor_scores.items(), key=lambda x: x[1])
    weakest_name, weakest_score = sorted_factors[0]
    second_weakest_name = sorted_factors[1][0] if len(sorted_factors) > 1 else None

    tips = {
        "regularity": (
            "Your biggest scoring gap is income consistency. "
            "Even small daily earnings on slow days reduce your variability score significantly — "
            "a ₹200 delivery shift on an otherwise idle day matters more than its face value."
        ),
        "income_floor": (
            "Your weakest factor is your income floor — some weeks had very low earnings. "
            "Lenders stress-test against your worst periods, not your average. "
            "Reducing the frequency of near-zero weeks (even by one per month) directly improves this score."
        ),
        "trend_momentum": (
            "Your trend score is limited by a flat or declining earnings direction. "
            "If your primary platform is slow, adding a second app for even 3–4 hours/week "
            "can reverse the trend signal within 6 weeks."
        ),
        "diversification": (
            "You currently rely on a single income platform — the highest-risk concentration profile. "
            "Lenders heavily penalise this: if that platform reduces rates or availability, "
            "your entire income is affected. Adding even one secondary platform raises this score significantly."
        ),
        "persistence": (
            "Your income shows low week-to-week predictability — "
            "good weeks don't reliably predict more good weeks. "
            "Building a minimum-hours commitment each week (even on slow days) "
            "creates the persistence signal that improves this factor."
        ),
    }

    if band == "Prime":
        weeks_needed = max(4, int((90 - score) / 2))
        return (
            f"Strong profile — {score:.0f}/100 puts you in the Prime tier, "
            f"qualifying for most loan and rental applications. "
            f"Maintaining this for {weeks_needed} more weeks strengthens your trailing average "
            f"and makes your report more compelling for larger loan amounts."
        )

    base_tip = tips.get(weakest_name, "Focus on building consistent weekly earnings.")

    if second_weakest_name and second_weakest_name != weakest_name:
        supplement = {
            "regularity": "Consistency is also below average.",
            "income_floor": "Your income floor also needs attention.",
            "trend_momentum": "Your trend direction is also dragging the score.",
            "diversification": "Platform diversification is also weak.",
            "persistence": "Week-to-week predictability is also low.",
        }.get(second_weakest_name, "")
        base_tip = f"{base_tip} {supplement}"

    return base_tip


# ══════════════════════════════════════════════════════════════════════════ #
#  Main entry point                                                         #
# ══════════════════════════════════════════════════════════════════════════ #

def compute_stability(transactions: list[dict]) -> dict:
    """
    Full five-factor stability computation.
    Returns a dict ready for storage in StabilityMetric.
    """
    income_txns = [
        t for t in transactions
        if float(t.get("credit", 0)) > 0
        and t.get("category") in INCOME_CATEGORIES
    ]

    if not income_txns:
        return _empty_result(transactions)

    # Build weekly income series
    df = pd.DataFrame(income_txns)
    df["txn_date"] = pd.to_datetime(df["txn_date"])
    df["credit"] = df["credit"].astype(float)
    df = df.set_index("txn_date").sort_index()

    weekly = df["credit"].resample("W").sum()

    # Fill weeks with no activity as zero (not NaN) — they are real zero-income weeks
    weekly = weekly.fillna(0.0)

    num_weeks = len(weekly)

    # ── Compute each factor ────────────────────────────────────────────────
    reg_score, reg_meta = _factor_regularity(weekly)
    floor_score, floor_meta = _factor_income_floor(weekly)
    trend_score, trend_meta = _factor_trend_momentum(weekly)
    div_score, div_meta = _factor_diversification(income_txns)
    persist_score, persist_meta = _factor_persistence(weekly)

    factor_scores = {
        "regularity": float(reg_score),
        "income_floor": float(floor_score),
        "trend_momentum": float(trend_score),
        "diversification": float(div_score),
        "persistence": float(persist_score),
    }

    factor_meta = {
        "regularity": reg_meta,
        "income_floor": floor_meta,
        "trend_momentum": trend_meta,
        "diversification": div_meta,
        "persistence": persist_meta,
    }

    score = _composite_score(factor_scores)
    band = _score_band(score)
    explanation = _build_explanation(score, factor_scores, factor_meta, num_weeks)
    action_tip = _build_action_tip(score, factor_scores, factor_meta)

    # Platform breakdown (for PDF report and donut chart)
    platform_totals: dict[str, float] = {}
    for t in income_txns:
        cat = t.get("category", "Other")
        platform_totals[cat] = platform_totals.get(cat, 0) + float(t.get("credit", 0))

    # Robust summary stats for storage
    mean_weekly = float(weekly.mean())
    std_weekly = float(weekly.std()) if len(weekly) > 1 else 0.0
    cv_pct = round((std_weekly / mean_weekly * 100) if mean_weekly > 0 else 0.0, 2)
    trend_pct = round(
        trend_meta.get("slope_pct_per_week", 0.0), 4
    )

    period_start = df.index.min().date()
    period_end = df.index.max().date()

    return {
        "period_start": period_start,
        "period_end": period_end,

        # Core stats (kept for backward compatibility with existing schema)
        "mean_weekly_income": round(mean_weekly, 2),
        "income_variance": round(std_weekly, 2),
        "cv_pct": cv_pct,
        "trend_pct": trend_pct,

        # Composite score
        "stability_score": score,

        # Factor breakdown — stored in platform_breakdown JSONB field
        # (reusing existing column to avoid another migration)
        "platform_breakdown": platform_totals,

        # Text fields
        "explanation": explanation,
        "action_tip": action_tip,

        # Full factor detail — stored as part of action_tip JSON extension
        # We'll add a new column below for this
        "_factor_detail": {
            "score_band": band,
            "weights": WEIGHTS,
            "factor_scores": factor_scores,
            "factor_meta": factor_meta,
            "num_weeks_analysed": num_weeks,
        },
    }


def _empty_result(transactions: list[dict]) -> dict:
    dates = [t["txn_date"] for t in transactions if t.get("txn_date")]
    start = min(dates) if dates else date.today()
    end = max(dates) if dates else date.today()
    return {
        "period_start": start,
        "period_end": end,
        "mean_weekly_income": 0.0,
        "income_variance": 0.0,
        "cv_pct": 0.0,
        "trend_pct": 0.0,
        "stability_score": 0.0,
        "explanation": "No income transactions found in the uploaded statements.",
        "action_tip": "Upload your bank statements or UPI exports to generate your stability profile.",
        "platform_breakdown": {},
        "_factor_detail": {},
    }