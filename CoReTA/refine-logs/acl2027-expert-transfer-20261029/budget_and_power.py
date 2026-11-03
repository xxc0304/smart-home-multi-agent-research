"""Reproduce planning arithmetic only; no model calls, data generation or tests."""
from __future__ import annotations

import json
import math
from datetime import date


def main() -> None:
    power = []
    q = 0.30
    for n in (240, 600, 1000):
        power.append({
            "effective_independent_items": n,
            "discordance_assumption": q,
            "overall_difference_approx_mde_pp": round(2.8 * math.sqrt(q / n) * 100, 2),
            "balanced_two_strata_difference_approx_mde_pp": round(2.8 * math.sqrt(4 * q / n) * 100, 2),
        })
    budgets = []
    for tier, calls, mean_in, mean_out in (
        ("A", 2200, 3500, 900),
        ("low", 32000, 3500, 900),
        ("full_600_raw_items_scenario", 70000, 5000, 1400),
    ):
        prices = []
        for p_in, p_out in ((1.2, 4.0), (2.0, 6.0)):
            usd = calls * (mean_in * p_in + mean_out * p_out) / 1_000_000
            prices.append({"assumed_usd_per_million_in_out": [p_in, p_out],
                           "usd_with_35pct_reserve": round(usd * 1.35, 2),
                           "cny_at_planning_rate_8": round(usd * 1.35 * 8, 2)})
        budgets.append({"tier": tier, "estimated_calls": calls,
                        "million_input_output_tokens": [calls * mean_in / 1e6, calls * mean_out / 1e6],
                        "prices": prices})
    print(json.dumps({
        "scope": "planning_arithmetic_not_experimental_results",
        "assumptions": "two-sided .05, approximate 80pct power, q=.30; no cluster inflation; D balanced for interaction; FX=8 is a planning assumption",
        "days_from_20261029_to_20270104": (date(2027, 1, 4) - date(2026, 10, 29)).days,
        "power": power,
        "interaction_effective_n_for_10pp": math.ceil(4 * q * (2.8 / 0.10) ** 2),
        "interaction_effective_n_for_8pp": math.ceil(4 * q * (2.8 / 0.08) ** 2),
        "budgets": budgets,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
