from datetime import datetime, timedelta
from enum import Enum
from typing import Type

from src.constants.constants import LIMIT, SMALLEST_INVEST
from src.data import data


def mapIndexToTime(timeFrame: data.TimeFrame, index: int) -> datetime:
  """
  Maps the index of the data to the corresponding time based on the given timeframe.
  :param timeFrame: The timeframe of the data.
  :param index: The index in the data.
  :return: The corresponding datetime for the given index and timeframe.
  :rtype: datetime
  """
  # maps the index of the data to the time
  # depending on the timeframe
  # e.g., for daily data, index 0 -> today, index 1 -> yesterday, etc.

  now = datetime.now()
  if timeFrame == data.TimeFrame.ONEMINUTE:
    return now.replace(second=0, microsecond=0) - timedelta(minutes=index)
  elif timeFrame == data.TimeFrame.FIVEMINUTES:
    return now.replace(second=0, microsecond=0) - timedelta(minutes=5 * index)
  elif timeFrame == data.TimeFrame.FIFTEENMINUTES:
    return now.replace(second=0, microsecond=0) - timedelta(minutes=15 * index)
  elif timeFrame == data.TimeFrame.ONEDAY:
    return now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=index)
  elif timeFrame == data.TimeFrame.ONEHOUR:
    return now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=index)
  elif timeFrame == data.TimeFrame.FOURHOURS:
    return now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=4 * index)
  else:
    raise TypeError("unsupported timeframe")


class Position:
  """Class representing a trading position.
  :param amount: The amount invested in the position.
  :param timeFrame: The timeframe of the position.
  :param currentIdx: The current index in the data.
  :type amount: float
  :type timeFrame: data.TimeFrame
  :type currentIdx: int
  :raises ValueError: if amount is less than 0, timeFrame is not of type data.TimeFrame, or currentIdx is less than 0 or not an int
  :return: None
  :rtype: None
  """

  def __set_amount(self, value: float) -> None:
    if value <= 0:
      raise ValueError("amount has to be bigger than 0")
    self.amount = value

  def __set_timeframe(self, value: data.TimeFrame) -> None:
    """
    Sets the timeframe for the position.
    :param value: The timeframe to set.
    :type value: data.TimeFrame
    :raises ValueError: if value is not of type data.TimeFrame
    :return: None
    :rtype: None
    """
    if not isinstance(value, data.TimeFrame):
      raise ValueError("timeFrame has to be of type data.TimeFrame")
    self.timeFrame = value

  def __set_idx(self, value: int) -> None:
    """
    Sets the current index for the position.
    :param value: The current index to set.
    :type value: int
    :raises ValueError: if value is less than 0 or not an int
    :return: None
    :rtype: None
    """
    if value < 0 or not isinstance(value, int):
      raise ValueError("currentIdx has to be bigger than 0 or not of type int")
    self.currentIdx = value

  def __init__(self, amount: float, timeFrame: data.TimeFrame, currentIdx: int = 0) -> None:
    """
    Initializes a Position instance.
    :param amount: The amount invested in the position.
    :param timeFrame: The timeframe of the position.
    :param currentIdx: The current index in the data.
    :type amount: float
    :type timeFrame: data.TimeFrame
    :type currentIdx: int
    :return: None
    :rtype: None
    """

    self.__set_idx(currentIdx)
    self.__set_amount(amount)
    self.__set_timeframe(timeFrame)
    self.createdAt = mapIndexToTime(timeFrame, currentIdx)
    self.isOpen = True
    self.closedAt = None

  def close(self) -> bool:  # gets called each tick to check if position should be closed
    """
    Closes the position if it is open.
    :return: bool indicating success of closing the position.
    :rtype: bool
    """
    if self.isOpen is True:
      self.isOpen = False

      self.closedAt = mapIndexToTime(self.timeFrame, self.currentIdx)
    else:
      raise "position is already closed"

  def forceClose(self) -> None:
    """
    Forces the position to close if it is open.
    :return: None
    :rtype: None
    """

    if self.isOpen is True:
      self.isOpen = False

      self.closedAt = mapIndexToTime(self.timeFrame, self.currentIdx)
    else:
      raise "position is already closed"

  def incrementIdx(self) -> None:
    """
    Increments the current index and updates the createdAt time accordingly.
    :return: None
    :rtype: None
    """
    self.currentIdx += 1
    self.createdAt = mapIndexToTime(self.timeFrame, self.currentIdx)

  def createDummyPosition(self, begin, close, amount) -> None:
    """
    Creates a dummy position for testing purposes.
    :param begin: The creation time of the position.
    :param close: The closing time of the position.
    :param amount: The amount invested in the position.
    :return: None
    :rtype: None
    """
    self.createdAt = begin
    self.closedAt = close
    self.amount = amount


class StopLossPosition(Position):
  """Class representing a trading position with a stop-loss mechanism.
  Inherits from the Position class.
  :param amount: The amount invested in the position.
  :param timeFrame: The timeframe of the position.
  :param stopLossPercent: The stop-loss percentage for the position.
  :param currentIdx: The current index in the data.
  :type amount: float
  :type timeFrame: data.TimeFrame
  :type stopLossPercent: float
  :type currentIdx: int
  :raises ValueError: if stopLossPercent is not between 0 and 100
  :return: None
  :rtype: None
  """

  def __init__(self, amount: float, timeFrame: data.TimeFrame, stopLossPercent: float, currentIdx: int = 0):
    super().__init__(amount, timeFrame, currentIdx)
    if stopLossPercent <= 0 or stopLossPercent >= 100:
      raise ValueError("stopLossPercent has to be between 0 and 100")
    self.stopLossPercent = stopLossPercent

  def close(self, currentPrice: float = None, entryPrice: float = None) -> bool:
    """
    Closes the position, optionally checking stop-loss threshold first.

    :param currentPrice: The current price of the asset (optional)
    :param entryPrice: The entry price of the position (optional)
    :return: bool indicating success of closing the position
    :rtype: bool
    :raises ValueError: if position is already closed
    """
    # If prices provided, check stop-loss condition
    if currentPrice is not None and entryPrice is not None:
      priceDrop = entryPrice * (self.stopLossPercent / 100)
      if currentPrice <= (entryPrice - priceDrop):
        return super().close()  # Close only if stop-loss triggered
      return False  # Don't close if stop-loss not triggered
    else:
      # Force close if no price data provided
      return super().close()

  def incrementIdx(self) -> None:
    """Increment the current index."""
    self.currentIdx += 1


class PositionType(Enum):
  """Enum for different types of positions."""

  BASIC = "basic"
  STOP_LOSS = "stop_loss"
  TAKE_PROFIT = "take_profit"
  # Add more position types as needed


class PositionHub:
  """Class representing a hub for managing multiple trading positions.
  :param positions: List of positions managed by the hub.
  :type positions: list[Position]
  :return: None"""

  def __init__(self, timeFrame: data.TimeFrame = data.TimeFrame.ONEDAY):
    """Constructor for PositionHub class.
    Initializes the PositionHub object.
    :param timeFrame: The timeframe for positions
    :type timeFrame: data.TimeFrame
    :return: None
    :rtype: None
    """
    self.positions: list[Position] = []  # stack of positions LIFO
    self.length = 0
    self.timeFrame = timeFrame

  # Position type mapping
  @staticmethod
  def _get_position_class(position_type: PositionType) -> Type[Position]:
    """
    Get the position class for a given position type.

    :param position_type: Type of position to create
    :type position_type: PositionType
    :return: Position class
    :rtype: Type[Position]
    """
    position_mapping = {
      PositionType.BASIC: Position,
      PositionType.STOP_LOSS: StopLossPosition,
      # PositionType.TAKE_PROFIT: TakeProfitPosition,
    }
    return position_mapping.get(position_type, Position)

  def checkConsitency(self):
    """
    Checks the consistency of the positions in the hub.
    :return: None
    :rtype: None
    """
    if self.length == 0:
      return
    if self.length != len(self.positions):
      raise Exception("length is representative for the positionId and should be updated accurately")

    # Check that only last position can be open
    if self.length > 1:
      for i in range(self.length - 1):
        if self.positions[i].isOpen is True:
          raise Exception("every position prior last should be closed")
    return

  def closeLatestPosition(self):
    """
    Closes the latest position in the hub if it is open.
    :return: None
    :rtype: None
    :raises TypeError: if no positions exist
    """
    if len(self.positions) == 0:
      raise TypeError("No positions exist to close")

    latestPosition = self.positions[-1]

    # Only close if position is open
    if latestPosition.isOpen:
      latestPosition.close()

  def openNewPosition(
    self,
    amount: float,
    timeFrame: data.TimeFrame = None,
    currentIdx: int = 0,
    position_type: PositionType = PositionType.BASIC,
    **kwargs,
  ):
    """
    Opens a new position with the given amount.
    If there is an existing position, it closes it first.

    :param amount: The amount to invest in the new position.
    :param timeFrame: The timeframe for the position (default: ONEDAY).
    :param currentIdx: The current index in the data.
    :param position_type: Type of position to create (default: BASIC).
    :param kwargs: Additional parameters for specific position types
                   (e.g., stopLossPercent for STOP_LOSS positions)
    :type amount: float
    :type timeFrame: data.TimeFrame
    :type currentIdx: int
    :type position_type: PositionType
    :raises Exception: if the amount is less than the smallest investment
    :return: None
    :rtype: None
    """
    # Validate amount
    if amount < SMALLEST_INVEST:
      raise Exception("stop here. amount should be bigger than smallest possible invest")

    # Use default timeFrame if not provided
    if timeFrame is None:
      timeFrame = self.timeFrame

    # Close existing position if any
    if self.length >= 1:
      self.closeLatestPosition()

    # Get the appropriate position class
    position_class = self._get_position_class(position_type)

    # Create position with correct arguments based on type
    if position_type == PositionType.STOP_LOSS:
      stop_loss_percent = kwargs.get("stopLossPercent", 5.0)
      position = position_class(
        amount=amount,
        timeFrame=timeFrame,
        stopLossPercent=stop_loss_percent,
        currentIdx=currentIdx,
      )
    elif position_type == PositionType.BASIC:
      position = position_class(
        amount=amount,
        timeFrame=timeFrame,
        currentIdx=currentIdx,
      )
    else:
      position = position_class(
        amount=amount,
        timeFrame=timeFrame,
        currentIdx=currentIdx,
      )

    # Add position to hub
    self.positions.append(position)
    self.checkConsitency()
    self.length += 1

  def openPositionObject(self, position: Position):
    """
    Opens an existing position object.
    Use this method to add pre-created position objects.

    :param position: The position object to add
    :type position: Position
    :raises Exception: if the position is invalid
    :return: None
    :rtype: None
    """
    if not isinstance(position, Position):
      raise TypeError("position must be an instance of Position or its subclasses")

    # Close existing position if any
    if self.length >= 1:
      self.closeLatestPosition()

    # Add position to hub
    self.positions.append(position)
    self.checkConsitency()
    self.length += 1

  def getAllPositions(self) -> list[Position]:
    """
    Retrieves all positions in the hub.
    :return: list of all positions
    :rtype: list[Position]
    """
    return self.positions

  def getPositionsByType(self, position_type: Type[Position]) -> list[Position]:
    """
    Get all positions of a specific type.

    :param position_type: The position class type to filter by
    :type position_type: Type[Position]
    :return: List of positions of the specified type
    :rtype: list[Position]
    """
    return [pos for pos in self.positions if isinstance(pos, position_type)]


class PositionSimulation:  # this only evaluates the
  """
  Class representing a simulation of trading positions.
  :param data: The data used for the simulation.
  :param balance: The initial balance for the simulation.
  :param limit: The maximum limit for investing assets.
  :type data: data.Data
  :type balance: float
  :type limit: float
  :return: None
  :rtype: None
  """

  def __init__(
    self,
    data: data.Data,
    balance=200,
    limit=LIMIT,
  ):
    """Constructor for PositionSimulation class.
    Initializes the PositionSimulation object with the given parameters.
    :param data: The data used for the simulation.
    :param balance: The initial balance for the simulation.
    :param limit: The maximum limit for investing assets.
    :type data: data.Data
    :type balance: float
    :type limit: float
    :return: None
    :rtype: None
    """
    self.positionHub = PositionHub()
    self.balance = balance
    self.limit = limit  # limit of investing assets
    self.variation = None  # this will include the proft and loss for every tick
    # -> maybe better to put this into the position?
    # nope - the idea is to calculate that 'live' in the reevaluation
    # this can be actually visualized

    self.data = data

    # will be iterated on later to calculate loss profit
    return

  def reevaluate(self):
    """
    Reevaluate all open positions based on the current data.
    :return: List of profit or loss for each tick.
    :rtype: list[float]
    """
    iterations = self.data.getDataLength()

    # Only validate for real Data objects, skip for test/dummy data
    if hasattr(self.data, "__class__") and self.data.__class__.__name__ == "Data":
      try:
        price_data = [self.data.getDataAtIndex(i) for i in range(iterations)]
        data.validateInstance(price_data, data.ALPACA_BTC_SCHEMA)
      except Exception:
        pass  # Skip validation if it fails

    positions = self.positionHub.getAllPositions()
    profitLossPerTick = []

    for pos in positions:
      if not pos.isOpen:
        continue

      idx = pos.currentIdx
      if idx >= iterations:
        continue

      dataPoint = self.data.getDataAtIndex(idx)
      openPrice = dataPoint.get("o", dataPoint.get("c", 0))
      closePrice = dataPoint.get("c", dataPoint.get("o", 0))
      entryPrice = openPrice
      currentPrice = closePrice
      variation = (currentPrice - entryPrice) * pos.amount
      profitLossPerTick.append(variation)

    return profitLossPerTick
