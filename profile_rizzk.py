#!/usr/bin/env python3
"""
Lightweight profiling harness for the RIZZK calculator core functions.
Runs a bunch of calculations in a loop to produce a cProfile file that's useful for hotspot analysis.
"""

from __future__ import annotations

import random
from time import perf_counter
from typing import Literal

from risk_reward_calculator.rizzk_core import (
    calculate_risk_reward,
    calculate_percentage_moves,
    calculate_risk_reward_ratio,
)


def run_heavy_load(iterations: int = 200_000) -> None:
    """Run a set of function calls that mimic calculator workload.

    Args:
        iterations: Number of iterations for the test workload. Reduce for faster runs.
    """
    # Keep deterministic but varied inputs for coverage of branches
    random.seed(42)

    start = perf_counter()
    acc_size_values = [1000.0, 10000.0, 25000.0, 100000.0]
    for i in range(iterations):
        account_size = acc_size_values[i % len(acc_size_values)]
        # Simulate small percent and fixed modes
        if i % 2 == 0:
            risk_mode: Literal["% of Account", "Fixed $ Amount"] = "% of Account"
            risk_input = float((i % 10) + 0.5)  # 0.5% -> 10.5%
        else:
            risk_mode = "Fixed $ Amount"
            risk_input = float((i % 50) + 1.0)  # $1 -> $50

        # Random price-like inputs within sensible ranges
        entry_price = 50.0 + (i % 100) * 0.1
        # stop loss near entry but not equal
        stop_price_offset = 0.5 + (i % 20) * 0.01
        if i % 2 == 0:
            # long position
            stop_loss = entry_price - stop_price_offset
            position_type = "Long"
        else:
            stop_loss = entry_price + stop_price_offset
            position_type = "Short"

        # Call core functions
        try:
            pos, pos_rounded, risk_amt, p1, p2, sl_amount = calculate_risk_reward(
                position_type,
                account_size,
                risk_mode,
                risk_input,
                entry_price,
                stop_loss,
            )
        except Exception:
            # If random input produced invalid case, skip
            continue

        # Compute derived metrics
        pct_drop, pct_move = calculate_percentage_moves(
            entry_price, stop_loss, p1, position_type
        )
        rr1 = calculate_risk_reward_ratio(entry_price, stop_loss, p1, position_type)

        # Avoid saving results; just a tiny bit of processing to mimic UI
        _ = (pos, pos_rounded, risk_amt, p1, p2, sl_amount, pct_drop, pct_move, rr1)

    end = perf_counter()
    print(f"Completed {iterations} iterations in {end - start:.2f}s")


if __name__ == "__main__":
    # Adjustable iterations via env or just default
    import os

    iters = int(os.environ.get("RIZZK_PROFILE_ITERATIONS", "200000"))
    run_heavy_load(iters)
