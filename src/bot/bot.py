from abc import ABC, abstractmethod
from typing import Optional

import src.position.position as position


class Bot(ABC):  # trading bot interface
  """
  Abstract base class for a trading bot interface.
  Provides methods to open and close positions, and to act on each tick of price data.
  """

  def __init__(self, name: str) -> None:
    """
    Initialize the bot with a name.

    :param name: Name identifier for the bot
    :type name: str
    :return: None
    :rtype: None
    """
    self.name = name

  @abstractmethod
  def closePosition(self, position: position.Position, priceData) -> bool:
    """
    Closes the given position based on the provided price data.
    Returns True if the position was successfully closed, False otherwise.
    :param position: The position to be closed.
    :param priceData: The price data used to determine the closing conditions.
    :return: bool indicating success of closing the position.
    """
    pass

  @abstractmethod
  def openPosition(self, priceData, currentIdx: int) -> Optional[position.Position]:
    """
    Opens a new position based on the provided price data and current index.
    Returns the newly opened position or None if no position is opened.
    :param priceData: The price data used to determine the opening conditions.
    :param currentIdx: The current index in the price data.
    :return: The newly opened position or None.
    """
    pass

  @abstractmethod
  def actOnTick(self, priceData, currentIdx: int) -> None:
    """
    Acts on each tick of price data at the given current index.
    :param priceData: The price data for the current tick.
    :param currentIdx: The current index in the price data.
    :return: None
    """
    pass
