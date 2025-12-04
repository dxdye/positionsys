from datetime import datetime, timedelta
from typing import Type

from src.constants.constants import LIMIT, SMALLEST_INVEST, OrderType, PositionType
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

  def _check_for_valid_close_price(self, value: float) -> None:
    if value is not None and value <= 0:
      raise ValueError("close_price has to be bigger than 0 - otherwise it be odd.")

  def _set_entry_price(self, value: float) -> None:
    if value <= 0:
      raise ValueError("entry_price has to be bigger than 0 - otherwise it be odd.")
    self.entry_price = value

  def _set_amount(self, value: float) -> None:
    if value <= 0:
      raise ValueError("amount has to be bigger than 0")
    self.amount = value

  def _set_timeframe(self, value: data.TimeFrame) -> None:
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

  def __init__(
    self,
    entry_price: float,
    amount: float,
    timeFrame: data.TimeFrame,
    orderType: OrderType = OrderType.LONG,
    currentIdx: int = 0,
  ) -> None:
    """
    Initializes a Position instance.
    :param amount: The amount of (shares, contracts, equity etc.) invested in the position.
    :param timeFrame: The timeframe of the position.
    :param currentIdx: The current index in the data.
    :type amount: float
    :type timeFrame: data.TimeFrame
    :type currentIdx: int
    :return: None
    :rtype: None
    """

    self._set_amount(amount)
    self._set_timeframe(timeFrame)
    self._set_entry_price(entry_price)
    self.createdAt = mapIndexToTime(
      timeFrame, currentIdx
    )  # time when position was created, adjusted to timeframe and index
    self.isOpen = True
    self.closedAt = None
    self.orderType = orderType
    self.positionType = PositionType.BASIC
    self.close_price = None

  def close(self, close_price: float):  # gets called each tick to check if position should be closed
    """
    Closes the position if it is open.
    :return: bool indicating success of closing the position.
    :rtype: bool
    """
    self._check_for_valid_close_price(close_price)
    if self.isOpen is True:
      self.isOpen = False
      self.closedAt = mapIndexToTime(self.timeFrame, self.currentIdx)
      self.close_price = close_price
    else:
      raise RuntimeError("position is already closed")

  def forceClose(self, close_price: float) -> None:
    """
    Forces the position to close if it is open.
    :return: None
    :rtype: None
    """
    self._check_for_valid_close_price(close_price)
    self.isOpen = False
    self.closedAt = mapIndexToTime(self.timeFrame, self.currentIdx)
    self.close_price = close_price

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

  def _set_stop_loss_percent(self, value: float) -> None:
    if value <= 0 or value >= 100:
      raise ValueError("stopLossPercent has to be between 0 and 100")
    self.stopLossPercent = value

  def __init__(
    self,
    amount: float,
    timeFrame: data.TimeFrame,
    stopLossPercent: float,
    orderType: OrderType = OrderType.LONG,
  ):
    super().__init__(amount=amount, timeFrame=timeFrame, orderType=orderType)
    self._set_stop_loss_percent(stopLossPercent)

  def close(self, close_price: float = None):
    """
    Closes the position if the current price falls below the stop-loss threshold.
    :param close_price: The current price of the asset (optional for force close).
    :param entryPrice: The entry price of the position (optional for force close).
    :return: bool indicating if position was closed
    :rtype: bool
    :raises ValueError: if position is already closed
    """
    if close_price is None or close_price <= 0:
      raise ValueError("close_price has to be provided and bigger than 0 for stop-loss evaluation")

    # If prices provided, check stop-loss condition
    if close_price is not None and self.entry_price is not None:
      priceDrop = self.entry_price * (self.stopLossPercent / 100)
      if close_price <= (self.entry_price - priceDrop) and self.orderType == OrderType.LONG:
        # Stop-loss triggered, close the position
        super().close()
      # else: stop-loss not triggered, don't close but still increment
      elif close_price >= (self.entry_price + priceDrop) and self.orderType == OrderType.SHORT:
        # Stop-loss triggered for short position, close the position
        super().close()

  def forceClose(self, close_price) -> None:
    """
    Forces the position to close.
    :return: None
    :rtype: None
    """
    super().forceClose(close_price)


class PositionHub:
  """Class representing a hub for managing multiple trading positions.
  Allows for more than one position at a time
  however only one position can be open at a time.
  :param timeFrame: The timeframe for positions in the hub.
  :type timeFrame: data.TimeFrame
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
    self.positions: list[Position] = []
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

  def checkConsistency(self):
    """
    Checks the consistency of the positions in the hub.
    :return: None
    :rtype: None
    """
    if self.length == 0:
      return
    if self.length != len(self.positions):
      raise Exception("length is representative for the positionId and should be updated accurately")

  def closeLatestPosition(self, close_price: float):
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
      latestPosition.close(close_price)

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
    self.checkConsistency()
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
    self.checkConsistency()
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


class PositionManagement:  # this only evaluates the
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

  def _set_tax_rate(self, tax_rate: float):
    """
    Sets the tax rate for the simulation.
    :param tax_rate: The tax rate to set.
    :type tax_rate: float
    :return: None
    """
    if tax_rate < 0 or tax_rate > 1:
      raise ValueError("tax_rate must be between 0 and 1")
    self.tax_rate = tax_rate

  def __init__(
    self,
    data: data.Data,
    balance=200,
    limit=LIMIT,
    tax_rate=0.0,
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
    self._set_tax_rate(tax_rate)
    self.data = data

    # will be iterated on later to calculate loss profit
    return

  def closeAllPositionsOnCondition(self):
    """
    Loops through all positions and close them if conditions are met
    :return: None
    :rtype: None
    """
    for pos in self.positionHub.getAllPositions():
      if pos.positionType == PositionType.STOP_LOSS and pos.isOpen:
        dataPoint = self.data.getDataAtIndex(pos.currentIdx)
        currentPrice = dataPoint.get("c", dataPoint.get("o", 0))
        pos.close(currentPrice=currentPrice)

  def closeAllRemainingOpenPositions(self):
    """
    Closes all remaining open positions, if simulation ends.
    :return: None
    :rtype: None
    """
    positions = self.positionHub.getAllPositions()
    for pos in positions:
      pos.forceClose()

  def evaluate(self):
    """
    Evaluate all open positions based on the current data.
    :return: List of profit or loss for each tick.
    :rtype: list[float]
    """

    positions = self.positionHub.getAllPositions()
    profitLossPerTick = []

    for pos in positions:
      if pos.orderType == OrderType.LONG:
        profit = (pos.close_price - pos.entry_price) * pos.amount
        profit = profit * (1 - self.tax_rate)  # apply tax
      elif pos.orderType == OrderType.SHORT:
        profit = (pos.entry_price - pos.close_price) * pos.amount
        profit = profit * (1 - self.tax_rate)  # apply tax
      else:
        profit = 0
      profitLossPerTick.append(profit)

    return profitLossPerTick
