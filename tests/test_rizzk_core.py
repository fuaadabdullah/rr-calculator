import math
import sys
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
MODULE_DIR = TESTS_DIR.parent
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

from rizzk_core import (
    calculate_percentage_moves,
    calculate_risk_reward,
    calculate_risk_reward_ratio,
)


class RiskCoreTests(unittest.TestCase):
    def test_calculate_risk_reward_long_percent(self):
        position_size, rounded, risk_amount, profit_1_1, profit_2_1, stop_amount = (
            calculate_risk_reward(
                position_type="Long",
                account_size=10_000,
                risk_mode="% of Account",
                risk_input=1.0,
                entry_price=100.0,
                stop_loss=95.0,
            )
        )

        self.assertTrue(math.isclose(position_size, 20.0, rel_tol=1e-6))
        self.assertEqual(rounded, 20)
        self.assertTrue(math.isclose(risk_amount, 100.0, rel_tol=1e-6))
        self.assertTrue(math.isclose(profit_1_1, 105.0, rel_tol=1e-6))
        self.assertTrue(math.isclose(profit_2_1, 110.0, rel_tol=1e-6))
        self.assertTrue(math.isclose(stop_amount, 100.0, rel_tol=1e-6))

    def test_calculate_risk_reward_short_fixed_amount(self):
        position_size, rounded, risk_amount, profit_1_1, profit_2_1, stop_amount = (
            calculate_risk_reward(
                position_type="Short",
                account_size=12_500,
                risk_mode="Fixed $ Amount",
                risk_input=250.0,
                entry_price=100.0,
                stop_loss=105.0,
            )
        )

        self.assertTrue(math.isclose(position_size, 50.0, rel_tol=1e-6))
        self.assertEqual(rounded, 50)
        self.assertTrue(math.isclose(risk_amount, 250.0, rel_tol=1e-6))
        self.assertTrue(math.isclose(profit_1_1, 95.0, rel_tol=1e-6))
        self.assertTrue(math.isclose(profit_2_1, 90.0, rel_tol=1e-6))
        self.assertTrue(math.isclose(stop_amount, 250.0, rel_tol=1e-6))

    def test_calculate_risk_reward_invalid_inputs(self):
        cases = [
            (
                dict(
                    position_type="Long",
                    account_size=5_000,
                    risk_mode="% of Account",
                    risk_input=1.0,
                    entry_price=100.0,
                    stop_loss=100.0,
                ),
                "Entry price and stop loss cannot be the same.",
            ),
            (
                dict(
                    position_type="Short",
                    account_size=5_000,
                    risk_mode="Fixed $ Amount",
                    risk_input=300.0,
                    entry_price=100.0,
                    stop_loss=95.0,
                ),
                "Entry price must be lower than stop loss for short positions.",
            ),
        ]

        for kwargs, message in cases:
            with self.assertRaisesRegex(ValueError, message):
                calculate_risk_reward(**kwargs)

    def test_calculate_percentage_moves_long_and_short(self):
        long_drop, long_move = calculate_percentage_moves(
            100.0, 95.0, 105.0, position_type="Long"
        )
        self.assertTrue(math.isclose(long_drop, 5.0, rel_tol=1e-6))
        self.assertTrue(math.isclose(long_move, 5.0, rel_tol=1e-6))

        short_drop, short_move = calculate_percentage_moves(
            100.0, 105.0, 95.0, position_type="Short"
        )
        self.assertTrue(math.isclose(short_drop, 5.0, rel_tol=1e-6))
        self.assertTrue(math.isclose(short_move, 5.0, rel_tol=1e-6))

    def test_calculate_risk_reward_ratio_round_trip(self):
        rr_long = calculate_risk_reward_ratio(100.0, 95.0, 110.0, position_type="Long")
        self.assertTrue(math.isclose(rr_long, 2.0, rel_tol=1e-6))

        rr_short = calculate_risk_reward_ratio(
            100.0, 105.0, 90.0, position_type="Short"
        )
        self.assertTrue(math.isclose(rr_short, 2.0, rel_tol=1e-6))

    def test_calculate_risk_reward_edge_cases(self):
        """Test edge cases for risk-reward calculations."""
        # Very small account size
        position_size, rounded, risk_amount, profit_1_1, profit_2_1, stop_amount = (
            calculate_risk_reward(
                position_type="Long",
                account_size=1.0,
                risk_mode="% of Account",
                risk_input=1.0,
                entry_price=100.0,
                stop_loss=99.0,
            )
        )
        self.assertTrue(
            math.isclose(position_size, 0.01, rel_tol=1e-6)
        )  # 1% of $1 = $0.01 risk, $1 spread = 0.01 shares
        self.assertEqual(rounded, 0)

        # Very large account size
        position_size, rounded, risk_amount, profit_1_1, profit_2_1, stop_amount = (
            calculate_risk_reward(
                position_type="Long",
                account_size=1_000_000,
                risk_mode="% of Account",
                risk_input=0.01,  # 0.01% risk = $100 risk
                entry_price=100.0,
                stop_loss=99.0,  # $1 spread
            )
        )
        self.assertTrue(
            math.isclose(position_size, 100.0, rel_tol=1e-6)
        )  # 100 / 1 = 100 shares

        # Very tight stop loss
        position_size, rounded, risk_amount, profit_1_1, profit_2_1, stop_amount = (
            calculate_risk_reward(
                position_type="Long",
                account_size=10000.0,
                risk_mode="Fixed $ Amount",
                risk_input=1.0,  # $1 risk
                entry_price=100.0,
                stop_loss=99.99,  # Very tight stop
            )
        )
        self.assertTrue(math.isclose(position_size, 100.0, rel_tol=1e-6))

    def test_calculate_risk_reward_boundary_conditions(self):
        """Test boundary conditions that should work."""
        # Minimum valid risk percentage
        position_size, rounded, risk_amount, profit_1_1, profit_2_1, stop_amount = (
            calculate_risk_reward(
                position_type="Long",
                account_size=10000.0,
                risk_mode="% of Account",
                risk_input=0.01,  # 0.01% minimum
                entry_price=100.0,
                stop_loss=99.0,
            )
        )
        self.assertTrue(math.isclose(risk_amount, 1.0, rel_tol=1e-6))

        # Maximum valid risk percentage
        position_size, rounded, risk_amount, profit_1_1, profit_2_1, stop_amount = (
            calculate_risk_reward(
                position_type="Long",
                account_size=10000.0,
                risk_mode="% of Account",
                risk_input=100.0,  # 100% risk
                entry_price=100.0,
                stop_loss=99.0,
            )
        )
        self.assertTrue(math.isclose(risk_amount, 10000.0, rel_tol=1e-6))

    def test_calculate_risk_reward_invalid_boundary_cases(self):
        """Test invalid boundary cases that should raise errors."""
        invalid_cases = [
            # Zero or negative account size
            (
                dict(
                    position_type="Long",
                    account_size=0,
                    risk_mode="% of Account",
                    risk_input=1.0,
                    entry_price=100.0,
                    stop_loss=99.0,
                ),
                "Account size must be greater than 0.",
            ),
            (
                dict(
                    position_type="Long",
                    account_size=-1000.0,
                    risk_mode="% of Account",
                    risk_input=1.0,
                    entry_price=100.0,
                    stop_loss=99.0,
                ),
                "Account size must be greater than 0.",
            ),
            # Zero or negative entry price
            (
                dict(
                    position_type="Long",
                    account_size=10000.0,
                    risk_mode="% of Account",
                    risk_input=1.0,
                    entry_price=0,
                    stop_loss=99.0,
                ),
                "Entry price must be greater than 0.",
            ),
            # Zero or negative stop loss
            (
                dict(
                    position_type="Long",
                    account_size=10000.0,
                    risk_mode="% of Account",
                    risk_input=1.0,
                    entry_price=100.0,
                    stop_loss=0,
                ),
                "Stop loss price must be greater than 0.",
            ),
            # Risk percentage out of bounds
            (
                dict(
                    position_type="Long",
                    account_size=10000.0,
                    risk_mode="% of Account",
                    risk_input=0,
                    entry_price=100.0,
                    stop_loss=99.0,
                ),
                "Risk percentage must be between 0 and 100.",
            ),
            (
                dict(
                    position_type="Long",
                    account_size=10000.0,
                    risk_mode="% of Account",
                    risk_input=101.0,
                    entry_price=100.0,
                    stop_loss=99.0,
                ),
                "Risk percentage must be between 0 and 100.",
            ),
            # Fixed risk amount out of bounds
            (
                dict(
                    position_type="Long",
                    account_size=10000.0,
                    risk_mode="Fixed $ Amount",
                    risk_input=0,
                    entry_price=100.0,
                    stop_loss=99.0,
                ),
                "Risk amount must be greater than 0.",
            ),
            (
                dict(
                    position_type="Long",
                    account_size=10000.0,
                    risk_mode="Fixed $ Amount",
                    risk_input=15000.0,  # More than account size
                    entry_price=100.0,
                    stop_loss=99.0,
                ),
                "Risk amount cannot exceed account size.",
            ),
            # Stop loss too close to entry (insane position size)
            (
                dict(
                    position_type="Long",
                    account_size=10000.0,
                    risk_mode="Fixed $ Amount",
                    risk_input=100.0,
                    entry_price=100.0,
                    stop_loss=99.99999,  # Extremely tight stop to trigger > 1M shares
                ),
                "Your stop is basically at entry. That's not a trade, that's a wish.",
            ),
        ]

        for kwargs, message in invalid_cases:
            with self.assertRaisesRegex(ValueError, message):
                calculate_risk_reward(**kwargs)

    def test_calculate_percentage_moves_edge_cases(self):
        """Test edge cases for percentage moves calculation."""
        # Very small moves
        drop, move = calculate_percentage_moves(
            100.0, 99.999, 100.001, position_type="Long"
        )
        self.assertTrue(math.isclose(drop, 0.001, rel_tol=1e-6))
        self.assertTrue(math.isclose(move, 0.001, rel_tol=1e-6))

        # Large moves
        drop, move = calculate_percentage_moves(
            100.0, 50.0, 200.0, position_type="Long"
        )
        self.assertTrue(math.isclose(drop, 50.0, rel_tol=1e-6))
        self.assertTrue(math.isclose(move, 100.0, rel_tol=1e-6))

    def test_calculate_risk_reward_ratio_edge_cases(self):
        """Test edge cases for risk-reward ratio calculation."""
        # Zero risk (should return 0 to avoid division by zero)
        ratio = calculate_risk_reward_ratio(100.0, 100.0, 110.0, position_type="Long")
        self.assertEqual(ratio, 0)

        # Very small risk
        ratio = calculate_risk_reward_ratio(100.0, 99.999, 110.0, position_type="Long")
        self.assertTrue(ratio > 1000)  # Should be very large

        # Break-even target
        ratio = calculate_risk_reward_ratio(100.0, 95.0, 100.0, position_type="Long")
        self.assertEqual(ratio, 0)

        # Loss target (negative ratio)
        ratio = calculate_risk_reward_ratio(100.0, 95.0, 97.5, position_type="Long")
        self.assertTrue(
            math.isclose(ratio, -0.5, rel_tol=1e-6)
        )  # 2.5 loss / 5 risk = -0.5


if __name__ == "__main__":
    unittest.main()
