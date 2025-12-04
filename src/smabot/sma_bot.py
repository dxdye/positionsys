"""
Simple Moving Average (SMA) Bot for algorithmic trading.
Implements SMA crossover strategy for automated buy/sell signals.
"""

from typing import Dict, List, Optional, Tuple, override

from src.bot.bot import Bot
from src.constants.constants import BotAction
from src.data.data import Data, TimeFrame
from src.position.position import PositionHub, PositionSimulation, PositionType


class SMABot(Bot):
  """
  A trading Bot that uses Simple Moving Average (SMA) crossover strategy.

  The Bot generates BUY signals when the short-term SMA crosses above the long-term SMA,
  and SELL signals when the short-term SMA crosses below the long-term SMA.

  :param name: Name of theBot
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
    super().__init__(name)

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

    self.simulation: PositionSimulation = PositionSimulation(data)
    self.short_window: int = short_window
    self.long_window: int = long_window
    self.stop_loss_percent: float = stop_loss_percent
    self.amount: float = amount
    self.in_position: bool = False
    self.last_entry_idx: int = 0
    self.timeFrame: Optional[TimeFrame] = getattr(data, "timeFrame", None)
    self.data = data

  def calculate_sma(self, prices: List[float], window: int) -> Optional[float]:
    """
    Calculate the Simple Moving Average for a given window.
    This function only exists in the SMABot class to encapsulate SMA logic.

    :param prices: List of prices
    :param window: Window size for SMA calculation
    :return: SMA value or None if not enough data points
    :rtype: Optional[float]
    """
    if not prices or len(prices) < window:
      return None
    return sum(prices[-window:]) / window

  @override
  def decide_and_trade(self, prices: List[float], current_idx: int) -> BotAction:
    """
    Decide whether to buy or sell based on SMA crossover strategy.

    :param prices: List of closing prices up to current index (inclusive)
    :param current_idx: Current index in the data
    :return: Trading decision - "BUY", "SELL", or "HOLD"
    :rtype: str
    """
    short_sma = self.calculate_sma(prices, self.short_window)
    long_sma = self.calculate_sma(prices, self.long_window)

    # Not enough data for both SMAs
    if short_sma is None or long_sma is None:
      return "HOLD"

    current_price = prices[-1]

    # Buy signal: short SMA crosses above long SMA and not currently in position
    if not self.in_position and short_sma > long_sma:
      return self._open_position(current_idx, current_price)

    # Sell signal: short SMA crosses below long SMA and currently in position
    if self.in_position and short_sma < long_sma:
      return self._close_position(current_idx, current_price)

    return BotAction.HOLD

  @override
  def _open_position(self, current_idx: int, current_price: float) -> BotAction:
    """
    Open a new position with stop loss.

    :param current_idx: Current index in the data
    :param current_price: Current price
    :return: "BUY" if successful, "HOLD" otherwise
    :rtype: str
    """
    try:
      self.position_hub.openNewPosition(
        amount=self.amount,
        timeFrame=self.timeFrame,
        currentIdx=current_idx,
        position_type=PositionType.STOP_LOSS,
        stopLossPercent=self.stop_loss_percent,
      )
      self.in_position = True
      self.last_entry_idx = current_idx
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
    Close the latest position.

    :param current_idx: Current index in the data
    :param current_price: Current price
    :return:  BotAction.SELL if successful,  BotAction.HOLD otherwise
    :rtype: BotAction
    """
    try:
      self.position_hub.closeLatestPosition()
      self.in_position = False
      self.trade_history.append(
        {
          "type": "SELL",
          "idx": current_idx,
          "price": current_price,
        }
      )
      return BotAction.SELL
    except Exception as e:
      print(f"Error closing position: {e}")
      return BotAction.HOLD

  @override
  def _should_open_position(self, prices: List[float]) -> bool:
    """
    Determine if a new position should be opened.

    :param prices: List of prices
    :return: True if position should be opened, False otherwise
    :rtype: bool
    """
    if self.in_position or len(prices) < self.long_window:
      return False

    short_sma = self.calculate_sma(prices, self.short_window)
    long_sma = self.calculate_sma(prices, self.long_window)

    return short_sma is not None and long_sma is not None and short_sma > long_sma

  @override
  def run(self) -> Tuple[List[Dict], float]:
    """
    Run the Bot through all data points and execute trades.

    Iterates through all price data and calls actOnTick for each point,
    which in turn calls decide_and_trade to handle all trading logic.

    :return: Tuple of (trade_history, profit_loss)
    :rtype: Tuple[List[Dict], float]
    """
    closing_prices = [self.simulation.data.getDataAtIndex(i)["c"] for i in range(self.simulation.data.getDataLength())]

    # Execute trades on each tick
    for idx in range(self.long_window, len(closing_prices)):
      window_prices = closing_prices[: idx + 1]
      self.actOnTick(window_prices, idx)

    # Evaluate profit/loss - reevaluate() returns a list of P/L per tick
    profit_loss_list = self.simulation.reevaluate()

    # Sum all profit/loss values to get total P/L
    total_profit_loss = sum(profit_loss_list) if profit_loss_list else 0.0

    return self.trade_history, total_profit_loss

  @override
  def reset(self) -> None:
    """Reset the Bot to its initial state."""
    self.position_hub = PositionHub()
    self.in_position = False
    self.last_entry_idx = 0
    self.trade_history = []
