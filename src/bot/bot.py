from abc import ABC, abstractmethod
from typing import Dict, List, Tuple

from src.constants.constants import BotAction
from src.position.position import Position, PositionHub


class Bot(ABC):  # trading bot interface
  """
  Abstract base class for a trading bot interface.
  Provides methods to open and close positions, and to act on each tick of price data.
  """

  def __init__(self, name: str) -> None:
    """
    Initialize the bot with a name.

    every bot has an instance of PositionHub (or a Subclass of it) to manage positions.
    it also has a trade history to log all executed trades.

    :param name: Name identifier for the bot
    :type name: str
    :return: None
    :rtype: None
    """

    self.name = name
    self.trade_history: List[Dict] = []

    self.position_hub: PositionHub = PositionHub()

  @abstractmethod
  def _close_position(self, current_idx: int, current_price: float) -> BotAction:
    """
    Mandatory and private: Close the latest position.
    Utilizes the position hub to close the latest position

    :param current_idx: Current index in the data
    :param current_price: Current price
    :return: "SELL" if successful, "HOLD" otherwise
    :rtype: BotAction
    """

  @abstractmethod
  def _open_position(self, current_idx: int, current_price: float) -> BotAction:
    """
    Mandatory and private: Open a new position.
    The percentage of the stop loss is bot-specific.
    Utilizes the position hub to open a new position
    The amount has to be determined by the bot.

    :param current_idx: Current index in the data
    :param current_price: Current price
    :return: "BUY" if successful, "HOLD" otherwise
    :rtype: str
    """

  @abstractmethod
  def _should_open_position(self, prices: List[float]) -> bool:
    """
    Mandatory and private: Determine if a new position should be opened.

    :param prices: List of prices
    :return: True if position should be opened, False otherwise
    :rtype: bool
    """

  @abstractmethod
  def decide_and_trade(self, prices: List[float], current_idx: int) -> BotAction:
    """
    Mandatory: Decide whether to open or close a position based on the provided prices
    and current index. Executes the trade if conditions are met.

    :param prices: List of prices
    :param current_idx: Current index in the data
    :return: "BUY", "SELL", or "HOLD" based on the decision
    :rtype: str
    """

  @abstractmethod
  def run(self) -> Tuple[List[Dict], float]:
    """
    Mandatory: Run the Bot through all data points and execute trades.
    It is the actual SIMULATION
    Utilizes the decide_and_trade method for each tick.
    Also it reevaluates all positions at the end to calculate profit/loss.
    And the returns as Tuple of trade history and profit/loss (float).
    That means it will evaluate all positions at the end of the data to close them and calculate
    For better understand the run method, look at the SMABot implementation.

    :return: Tuple of (trade_history, profit_loss)
    :rtype: Tuple[List[Dict], float]
    """

  @abstractmethod
  def reset(self) -> None:
    """
    Somewhat optional: Define a reset function for testing or re-running the bot.
    Might also be useful to implement UI reset functionality.
    """

  # Getter
  def get_trade_history(self) -> List[Dict]:
    """
    Get the Bot's trade history.

    :return: List of all trades executed
    :rtype: List[Dict]
    """
    return self.trade_history

  def get_open_positions_count(self) -> int:
    """
    Get the number of currently open positions.

    :return: Number of open positions
    :rtype: int
    """
    return len([p for p in self.get_positions() if p.isOpen])

  def get_positions(self) -> List[Position]:
    """
    Get all positions managed by the Bot.

    :return: List of all positions
    :rtype: List[Position]
    """
    return self.position_hub.getAllPositions()

  def actOnTick(self, priceData: List[float], currentIdx: int) -> None:
    """
    Implementation of abstract method from bot interface.
    Acts on each tick of price data using the SMA crossover strategy.

    This method is called for each new price data point and orchestrates
    the trading decisions.

    :param priceData: Price data available up to current index (inclusive)
    :param currentIdx: Current index in the price data
    :return: None
    :rtype: None
    """
    try:
      self.decide_and_trade(priceData, currentIdx)
      # Decision is already handled by decide_and_trade
      # No need to do anything else here
    except Exception as e:
      print(f"Error in actOnTick at index {currentIdx}: {type(e).__name__}: {e}")
      import traceback

      traceback.print_exc()
