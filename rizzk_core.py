#!/usr/bin/env python3
"""
Core calculation functions for the RIZZK Risk-to-Reward Calculator.
Centralized math logic for position sizing and risk management.
"""

from typing import Literal


def calculate_risk_reward(
    position_type: Literal["Long", "Short"],
    account_size: float,
    risk_mode: Literal["% of Account", "Fixed $ Amount"],
    risk_input: float,
    entry_price: float,
    stop_loss: float
) -> tuple[float, float, float, float, float, float]:
    """
    Calculate position size, risk amount, and profit targets.

    Args:
        position_type (Literal["Long", "Short"]): "Long" or "Short"
        account_size (float): Total account size in dollars
        risk_mode (Literal["% of Account", "Fixed $ Amount"]): Risk calculation mode
        risk_input (float): Risk percentage (0-100) if risk_mode is "% of Account", 
                           or fixed risk amount in dollars if "Fixed $ Amount"
        entry_price (float): Entry price
        stop_loss (float): Stop loss price

    Returns:
        tuple[float, float, float, float, float, float]: (position_size, position_size_rounded, 
                                                          risk_amount, profit_1_1, profit_2_1, stop_loss_amount)

    Raises:
        ValueError: If inputs are invalid
    """
    if account_size <= 0:
        raise ValueError("Account size must be greater than 0.")
    if entry_price <= 0:
        raise ValueError("Entry price must be greater than 0.")
    if stop_loss <= 0:
        raise ValueError("Stop loss price must be greater than 0.")
    if entry_price == stop_loss:
        raise ValueError("Entry price and stop loss cannot be the same.")
    
    # Calculate risk amount based on mode
    if risk_mode == "% of Account":
        if risk_input <= 0 or risk_input > 100:
            raise ValueError("Risk percentage must be between 0 and 100.")
        risk_amount = account_size * (risk_input / 100)
    else:  # Fixed $ Amount
        if risk_input <= 0:
            raise ValueError("Risk amount must be greater than 0.")
        if risk_input > account_size:
            raise ValueError("Risk amount cannot exceed account size.")
        risk_amount = risk_input

    if position_type == "Long":
        if entry_price <= stop_loss:
            raise ValueError("Entry price must be higher than stop loss for long positions.")
        position_size = risk_amount / (entry_price - stop_loss)
        stop_loss_amount = position_size * (entry_price - stop_loss)
        profit_1_1 = entry_price + (entry_price - stop_loss)
        profit_2_1 = entry_price + 2 * (entry_price - stop_loss)
    else:  # Short
        if entry_price >= stop_loss:
            raise ValueError("Entry price must be lower than stop loss for short positions.")
        position_size = risk_amount / (stop_loss - entry_price)
        stop_loss_amount = position_size * (stop_loss - entry_price)
        profit_1_1 = entry_price - (stop_loss - entry_price)
        profit_2_1 = entry_price - 2 * (stop_loss - entry_price)

    # Check for insane position sizes (stop loss too close to entry)
    if position_size > 1_000_000:
        raise ValueError("Your stop is basically at entry. That's not a trade, that's a wish.")

    # Calculate rounded position size (most brokers don't accept fractional shares)
    position_size_rounded = int(position_size)

    return position_size, position_size_rounded, risk_amount, profit_1_1, profit_2_1, stop_loss_amount
def calculate_percentage_moves(entry_price: float, stop_loss: float, profit_1_1: float, position_type: Literal["Long", "Short"] = "Long") -> tuple[float, float]:
    """
    Calculate percentage moves for stop loss and profit targets.

    Args:
        entry_price (float): Entry price
        stop_loss (float): Stop loss price
        profit_1_1 (float): 1:1 profit target
        position_type (Literal["Long", "Short"]): "Long" or "Short"

    Returns:
        tuple[float, float]: (pct_drop_to_stop, pct_move_to_1_1)
    """
    if position_type == "Long":
        pct_drop_to_stop = ((entry_price - stop_loss) / entry_price) * 100
        pct_move_to_1_1 = ((profit_1_1 - entry_price) / entry_price) * 100
    else:
        pct_drop_to_stop = ((stop_loss - entry_price) / entry_price) * 100
        pct_move_to_1_1 = ((entry_price - profit_1_1) / entry_price) * 100

    return pct_drop_to_stop, pct_move_to_1_1


def calculate_risk_reward_ratio(entry_price: float, stop_loss: float, profit_target: float, position_type: Literal["Long", "Short"] = "Long") -> float:
    """
    Calculate the risk-to-reward ratio for a given profit target.

    Args:
        entry_price (float): Entry price
        stop_loss (float): Stop loss price
        profit_target (float): Profit target price
        position_type (Literal["Long", "Short"]): "Long" or "Short"

    Returns:
        float: Risk-to-reward ratio
    """
    if position_type == "Long":
        risk = entry_price - stop_loss
        reward = profit_target - entry_price
    else:
        risk = stop_loss - entry_price
        reward = entry_price - profit_target

    return reward / risk if risk != 0 else 0