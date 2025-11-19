#!/usr/bin/env python3
"""
Unit tests for the RIZZK Risk-to-Reward Calculator core logic.
Uses unittest for proper test framework functionality.
"""

import unittest
from rizzk_core import calculate_risk_reward


class TestRiskRewardCalculator(unittest.TestCase):
    """Test cases for risk-reward calculation functions."""

    def test_long_basic(self):
        """Test basic long position calculations."""
        (
            position_size,
            position_size_rounded,
            risk_amount,
            profit_1_1,
            profit_2_1,
            stop_loss_amount,
        ) = calculate_risk_reward("Long", 10000.0, "% of Account", 1.0, 100.0, 95.0)

        self.assertAlmostEqual(risk_amount, 100.0, places=2)
        self.assertAlmostEqual(position_size, 20.0, places=2)
        self.assertEqual(position_size_rounded, 20)
        self.assertAlmostEqual(profit_1_1, 105.0, places=2)

    def test_short_basic(self):
        """Test basic short position calculations."""
        (
            position_size,
            position_size_rounded,
            risk_amount,
            profit_1_1,
            profit_2_1,
            stop_loss_amount,
        ) = calculate_risk_reward("Short", 10000.0, "% of Account", 1.0, 95.0, 100.0)

        self.assertAlmostEqual(risk_amount, 100.0, places=2)
        self.assertAlmostEqual(position_size, 20.0, places=2)
        self.assertEqual(position_size_rounded, 20)
        self.assertAlmostEqual(profit_1_1, 90.0, places=2)

    def test_fixed_dollar_mode_long(self):
        """Fixed $ mode should size by dollars at risk, independent of account percent."""
        # $100 risk on a $10,000 account, entry 100, stop 95 => $5 risk per share => 20 shares
        (
            position_size,
            position_size_rounded,
            risk_amount,
            profit_1_1,
            profit_2_1,
            stop_loss_amount,
        ) = calculate_risk_reward("Long", 10000.0, "Fixed $ Amount", 100.0, 100.0, 95.0)

        self.assertAlmostEqual(risk_amount, 100.0, places=2)
        self.assertAlmostEqual(position_size, 20.0, places=2)
        self.assertEqual(position_size_rounded, 20)
        self.assertAlmostEqual(profit_1_1, 105.0, places=2)

    def test_invalid_inputs_raise(self):
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
            (
                "Long",
                10000,
                "% of Account",
                1,
                100,
                99.99995,
            ),  # insane position size (> 1M)
            (
                "Short",
                10000,
                "% of Account",
                1,
                100,
                100.00005,
            ),  # insane position size short (> 1M)
        ]

        for case in invalid_cases:
            with self.assertRaises(ValueError):
                calculate_risk_reward(*case)

    def test_edge_case_values(self):
        """Test edge case with small values."""
        (
            position_size,
            position_size_rounded,
            risk_amount,
            profit_1_1,
            profit_2_1,
            stop_loss_amount,
        ) = calculate_risk_reward("Long", 1000.0, "% of Account", 0.1, 10.0, 9.9)

        self.assertGreater(position_size, 0)
        self.assertGreaterEqual(position_size_rounded, 0)  # Should be integer
        self.assertEqual(risk_amount, 1.0)

    def test_extreme_sanity_check(self):
        """Extreme sanity test: tiny account, microscopic risk, weird price levels.
        Ensures no crashes and no negative sizes - RIZZK is built for safety first."""
        # Extreme edge case: $1 account, 0.001% risk, weird decimal prices
        (
            position_size,
            position_size_rounded,
            risk_amount,
            profit_1_1,
            profit_2_1,
            stop_loss_amount,
        ) = calculate_risk_reward("Long", 1.0, "% of Account", 0.001, 0.0001, 0.00009)

        # Safety first: no negative values, no crashes
        self.assertGreaterEqual(position_size, 0)
        self.assertGreaterEqual(position_size_rounded, 0)
        self.assertGreaterEqual(risk_amount, 0)
        self.assertGreaterEqual(profit_1_1, 0)
        self.assertGreaterEqual(profit_2_1, 0)
        self.assertGreaterEqual(stop_loss_amount, 0)

        # Verify risk amount is correctly calculated (0.001% of $1 = $0.00001)
        self.assertAlmostEqual(risk_amount, 0.00001, places=8)

        # Position size should be reasonable (not infinite or negative)
        self.assertLess(position_size, 1e6)  # Sanity check: not insanely large


if __name__ == "__main__":
    unittest.main()
