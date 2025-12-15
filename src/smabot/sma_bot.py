"""
Simple Moving Average (SMA) Bot for algorithmic trading.
Implements SMA crossover strategy for automated buy/sell signals.
"""

from typing import Dict, List, Optional, Tuple, override

from src.bot.bot import Bot
from src.constants.constants import BotAction
from src.data.data import Data, TimeFrame
from src.position.position import PositionHub, PositionType


class SMABot(Bot):
  """
  A trading bot that uses Simple Moving Average (SMA) crossover strategy.

  The bot generates BUY signals when the short-term SMA crosses above the long-term SMA,
  and SELL signals when the short-term SMA crosses below the long-term SMA.

  This is a local trading bot that simulates a simple moving average strategy.
  It opens and closes stop loss positions, and only allows one open position at a time.

  :param name: Name of the bot
  :param data: Data object containing price data and timeframe
  :param short_window: Window size for short-term SMA (default: 40)
  :param long_window: Window size for long-term SMA (default: 100)
  :param stop_loss_percent: Stop-loss percentage for positions (default: 5.0%)
  :param amount: Amount to invest per position (default: 1.0)
  :type name: str
  :type data: Data
  :type short_window: int
  :type long_window: int
  :type stop_loss_percent: float
  :type amount: float
  """

  def __init__(
    self,
    name: str,
    data: Data,
    short_window: int = 40,
    long_window: int = 100,
    stop_loss_percent: float = 5.0,
    amount: float = 1.0,
  ) -> None:
    """Initialize the SMABot with parameters."""
    super().__init__(name, data)

    # Validate parameters
    if short_window >= long_window:
      raise ValueError("short_window must be less than long_window")
    if short_window <= 0 or long_window <= 0:
      raise ValueError("window sizes must be positive")
    if stop_loss_percent <= 0:
      raise ValueError("stop_loss_percent must be positive")
    if amount <= 0:
      raise ValueError("amount must be positive")

    # Extract and validate timeFrame
    timeFrame = getattr(data, "timeFrame", None)
    if timeFrame is None:
      raise ValueError("data object must have a valid timeFrame attribute")
    if not isinstance(timeFrame, TimeFrame):
      raise ValueError("data.timeFrame must be a TimeFrame enum")

    self.short_window: int = short_window
    self.long_window: int = long_window
    self.stop_loss_percent: float = stop_loss_percent
    self.amount: float = amount
    self.timeFrame: TimeFrame = timeFrame

  def calculate_sma(self, prices: List[float], window: int) -> Optional[float]:
    """
    Calculate the Simple Moving Average for a given window.

    :param prices: List of prices
    :param window: Window size for SMA calculation
    :return: SMA value or None if not enough data points
    :rtype: Optional[float]
    """
    if not prices or len(prices) < window:
      return None
    return sum(prices[-window:]) / window

  def _has_open_position(self) -> bool:
    """
    Check if there is currently an open position.

    :return: True if there is an open position, False otherwise
    :rtype: bool
    """
    open_positions = [p for p in self.position_management.position_hub.getAllPositions() if p.isOpen]
    return len(open_positions) > 0

  @override
  def decide_and_trade(self, prices: List[float], current_idx: int) -> BotAction:
    """
    Decide whether to buy or sell based on SMA crossover strategy.
    This method is called for each tick and implements the trading logic.

    IMPORTANT: Calls closeAllPositionsOnCondition for every tick to check stop-loss conditions.

    :param prices: List of closing prices up to current index (inclusive)
    :param current_idx: Current index in the data
    :return: Trading decision - BotAction.BUY, BotAction.SELL, or BotAction.HOLD
    :rtype: BotAction
    """
    # Kritisch: Check stop-loss conditions for all positions on every tick
    self.position_management.closeAllPositionsOnCondition(current_idx)

    # Calculate SMAs
    short_sma = self.calculate_sma(prices, self.short_window)
    long_sma = self.calculate_sma(prices, self.long_window)

    # Not enough data for both SMAs
    if short_sma is None or long_sma is None:
      return BotAction.HOLD

    current_price = prices[-1]
    has_open_position = self._has_open_position()

    # Buy signal: short SMA crosses above long SMA and NO open position
    if not has_open_position and short_sma > long_sma:
      return self._open_position(current_idx, current_price)

    # Sell signal: short SMA crosses below long SMA and we have an open position
    if has_open_position and short_sma < long_sma:
      return self._close_position(current_idx, current_price)

    return BotAction.HOLD

  @override
  def _open_position(self, current_idx: int, current_price: float) -> BotAction:
    """
    Open a new stop-loss position.
    Only one position is allowed at a time.

    :param current_idx: Current index in the data
    :param current_price: Current price
    :return: BotAction.BUY if successful, BotAction.HOLD otherwise
    :rtype: BotAction
    """
    try:
      # Ensure only one position at a time
      if self._has_open_position():
        return BotAction.HOLD

      self.position_management.position_hub.openNewPosition(
        entry_price=current_price,
        amount=self.amount,
        timeFrame=self.timeFrame,
        position_type=PositionType.STOP_LOSS,
        stopLossPercent=self.stop_loss_percent,
      )

      self.trade_history.append(
        {
          "type": BotAction.BUY,
          "idx": current_idx,
          "price": current_price,
        }
      )
      return BotAction.BUY
    except Exception as e:
      print(f"Error opening position: {type(e).__name__}: {e}")
      return BotAction.HOLD

  @override
  def _close_position(self, current_idx: int, current_price: float) -> BotAction:
    """
    Close the latest open position.

    :param current_idx: Current index in the data
    :param current_price: Current price
    :return: BotAction.SELL if successful, BotAction.HOLD otherwise
    :rtype: BotAction
    """
    try:
      if not self._has_open_position():
        return BotAction.HOLD

      self.position_management.position_hub.closeLatestPosition(current_price)

      self.trade_history.append(
        {
          "type": BotAction.SELL,
          "idx": current_idx,
          "price": current_price,
        }
      )
      return BotAction.SELL
    except Exception as e:
      print(f"Error closing position: {type(e).__name__}: {e}")
      return BotAction.HOLD

  @override
  def _should_open_position(self, prices: List[float]) -> bool:
    """
    Determine if a new position should be opened based on SMA crossover.

    :param prices: List of prices
    :return: True if position should be opened, False otherwise
    :rtype: bool
    """
    if self._has_open_position() or len(prices) < self.long_window:
      return False

    short_sma = self.calculate_sma(prices, self.short_window)
    long_sma = self.calculate_sma(prices, self.long_window)

    return short_sma is not None and long_sma is not None and short_sma > long_sma

  @override
  def reset(self) -> None:
    """Reset the bot to its initial state."""
    self.position_management.position_hub = PositionHub(self.timeFrame)
    self.trade_history = []

  @override
  def run(self) -> Tuple[List[Dict], float]:
    """
    Run the SMA Bot through all data points starting from long_window index.

    Overrides the base Bot.run() to start from long_window index since
    we need at least long_window data points to calculate the long SMA.

    :return: Tuple of (trade_history, profit_loss)
    :rtype: Tuple[List[Dict], float]
    """
    # Get data length once to avoid repeated calls
    data_length = self.position_management.data.getDataLength()

    # Get all closing prices once
    all_closing_prices = self.position_management.data.get_closing_prices()

    # Start from long_window since we need that many points for SMA calculation
    for idx in range(self.long_window, data_length):
      # Use closing prices up to current index
      window_prices = all_closing_prices[: idx + 1]
      self.actOnTick(window_prices, idx)

    # Close all remaining open positions at the end
    last_idx = data_length - 1
    if last_idx >= 0:
      self.position_management.closeAllRemainingOpenPositions(last_idx)

    # Evaluate profit/loss - reevaluate() returns a list of P/L per tick
    profit_loss_list = self.position_management.evaluate()

    # Sum all profit/loss values to get total P/L
    total_profit_loss = sum(profit_loss_list) if profit_loss_list else 0.0

    return self.trade_history, total_profit_loss
