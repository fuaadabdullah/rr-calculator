#!/usr/bin/env python3
"""
Unit tests for the RIZZK Risk-to-Reward Calculator core logic.
Uses pytest for proper test framework functionality.
"""

import pytest
from rizzk_core import calculate_risk_reward


def test_long_basic():
    """Test basic long position calculations."""
    position_size, position_size_rounded, risk_amount, profit_1_1, profit_2_1, stop_loss_amount = calculate_risk_reward(
        "Long", 10000.0, "% of Account", 1.0, 100.0, 95.0
    )

    assert abs(risk_amount - 100.0) < 0.01
    assert abs(position_size - 20.0) < 0.01
    assert position_size_rounded == 20
    assert abs(profit_1_1 - 105.0) < 0.01


def test_short_basic():
    """Test basic short position calculations."""
    position_size, position_size_rounded, risk_amount, profit_1_1, profit_2_1, stop_loss_amount = calculate_risk_reward(
        "Short", 10000.0, "% of Account", 1.0, 95.0, 100.0
    )

    assert abs(risk_amount - 100.0) < 0.01
    assert abs(position_size - 20.0) < 0.01
    assert position_size_rounded == 20
    assert abs(profit_1_1 - 90.0) < 0.01


def test_invalid_inputs_raise():
    """Test that invalid inputs raise ValueError."""
    invalid_cases = [
        ("Long", 0, "% of Account", 1, 100, 95),  # account <= 0
        ("Long", 10000, "% of Account", 0, 100, 95),  # risk <= 0
        ("Long", 10000, "% of Account", 101, 100, 95),  # risk > 100
        ("Long", 10000, "% of Account", 1, 0, 95),  # entry <= 0
        ("Long", 10000, "% of Account", 1, 100, 0),  # stop <= 0
        ("Long", 10000, "% of Account", 1, 100, 100),  # entry == stop
        ("Long", 10000, "% of Account", 1, 95, 100),  # long: entry <= stop
        ("Short", 10000, "% of Account", 1, 100, 95),  # short: entry >= stop
        ("Long", 10000, "% of Account", 1, 100, 99.99995),  # insane position size (> 1M)
        ("Short", 10000, "% of Account", 1, 100, 100.00005),  # insane position size short (> 1M)
    ]

    for case in invalid_cases:
        with pytest.raises(ValueError):
            calculate_risk_reward(*case)


def test_edge_case_values():
    """Test edge case with small values."""
    position_size, position_size_rounded, risk_amount, profit_1_1, profit_2_1, stop_loss_amount = calculate_risk_reward(
        "Long", 1000.0, "% of Account", 0.1, 10.0, 9.9
    )

    assert position_size > 0
    assert position_size_rounded >= 0  # Should be integer
    assert risk_amount == 1.0


def test_extreme_sanity_check():
    """Extreme sanity test: tiny account, microscopic risk, weird price levels.
    Ensures no crashes and no negative sizes - RIZZK is built for safety first."""
    # Extreme edge case: $1 account, 0.001% risk, weird decimal prices
    position_size, position_size_rounded, risk_amount, profit_1_1, profit_2_1, stop_loss_amount = calculate_risk_reward(
        "Long", 1.0, "% of Account", 0.001, 0.0001, 0.00009
    )

    # Safety first: no negative values, no crashes
    assert position_size >= 0
    assert position_size_rounded >= 0
    assert risk_amount >= 0
    assert profit_1_1 >= 0
    assert profit_2_1 >= 0
    assert stop_loss_amount >= 0

    # Verify risk amount is correctly calculated (0.001% of $1 = $0.00001)
    assert abs(risk_amount - 0.00001) < 1e-8

    # Position size should be reasonable (not infinite or negative)
    assert position_size < 1e6  # Sanity check: not insanely large