import sys

sys.path.append("../")
from datetime import datetime

import data.data as data

LIMIT = 10000
SMALLEST_INVEST = 0.01


def mapIndexToTime(timeFrame: data.TimeFrame, index: int) -> datetime:
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
    raise "unsupported timeframe"


def timedelta(**kwargs):
  return datetime.now() - datetime.now().replace(**kwargs)


class Position:
  def __set_amount(self, value: float) -> None:
    if value < 0:
      raise ValueError("amount has to be bigger than 0")
    self.amount = value

  def __set_timeframe(self, value: data.TimeFrame) -> None:
    if not isinstance(value, data.TimeFrame):
      raise ValueError("timeFrame has to be of type data.TimeFrame")
    self.timeFrame = value

  def __set_idx(self, value: int) -> None:
    if value < 0 or not isinstance(value, int):
      raise ValueError("currentIdx has to be bigger than 0 or not of type int")
    self.currentIdx = value

  def __init__(self, amount: float, timeFrame: data.TimeFrame, currentIdx: int = 0) -> None:
    self.createdAt = mapIndexToTime(timeFrame, currentIdx)
    self.isOpen = True
    self.closedAt = None

    self.__set_idx(currentIdx)
    self.__set_amount(amount)
    self.__set_timeframe(timeFrame)

  def close(self) -> bool:  # gets called each tick to check if position should be closed
    if self.isOpen is True:
      self.isOpen = False

      self.closedAt = mapIndexToTime(self.timeFrame, self.currentIdx)
    else:
      raise "position is already closed"

  def forceClose(self) -> None:
    if self.isOpen is True:
      self.isOpen = False

      self.closedAt = mapIndexToTime(self.timeFrame, self.currentIdx)
    else:
      raise "position is already closed"

  def incrementIdx(self) -> None:
    self.currentIdx += 1
    self.createdAt = mapIndexToTime(self.timeFrame, self.currentIdx)

  def createDummyPosition(self, begin, close, amount) -> None:
    self.createdAt = begin
    self.closedAt = close
    self.amount = amount


class StopLossPosition(Position):
  def __init__(self, amount: float, timeFrame: data.TimeFrame, stopLossPercent: float, currentIdx: int = 0):
    super().__init__(amount, timeFrame, currentIdx)
    if stopLossPercent <= 0 or stopLossPercent >= 100:
      raise "stopLossPercent has to be between 0 and 100"
    self.stopLossPercent = stopLossPercent

  def close(self, currentPrice: float, entryPrice: float) -> None:
    priceDrop = entryPrice * (self.stopLossPercent / 100)
    if currentPrice <= (entryPrice - priceDrop):
      super().close()
    self.incrementIdx()


class PositionHub:
  def __init__(
    self,
  ):
    self.positions: list[Position] = []  # stack of positions LIFO
    self.length = 0

  # open new position

  def checkConsitency(self):
    if self.length == 0:
      return
    if self.length != len(self.position):
      raise "length is representative for the positionId and should be updated accuratly"
    # is of type [position]
    # only last position can be open or closed
    # every other is closed
    # the one opened is not followed by any other
    for i in self.positions:
      if type(i) is not Position:
        raise "element is of wrong type"
    if self.length > 1:
      for i in range(self.position - 1):
        if self.positions[i].isOpen is True:
          raise "every position prior last should be closed"
    return

  def closeLatestPosition(self):
    self.checkConsitency()
    if len(self.positions) == 0:
      raise "no positions existant"

    latestPosition: Position = self.positions[-1]
    if not (latestPosition.isOpen):
      return  # latest position already closed - stop here.
    if self.latestPosition.closedAt is None:  ##dreifach hält besser
      self.latestPosition.close()

  def openNewPosition(self, amount):
    # close old position automatically
    if amount < SMALLEST_INVEST:
      raise "stop here. amount should be bigger than smallest possible invest"
    if self.length >= 1:  # when positions existant
      self.closeLatestPosition()
    self.positions.append(Position((amount, self.length + 1)))
    self.checkConsitency()
    self.length += 1  # id defined via length

  def getAllPositions(self):
    return self.positions


class PositionSimulation:  # this only evaluates the
  def __init__(
    self,
    data: data.Data,
    balance=200,
    limit=LIMIT,
  ):
    self.positionHub = PositionHub()
    self.balance = balance
    self.limit = limit  # limit of investing assets
    self.variation = None  # this will include the proft and loss for every tick
    # -> maybe better to put this into the position?
    # nope - the idea is to calculate that 'live' in the reevaluation
    # this can be actually visualized

    self.data = data

  # will be iterated on later to calculate loss profit

  def reevaluate(self):
    # Positionen operieren auf den Daten - Evaluation aller Positionen
    iterations = self.data.getDataLength()
    data.validateInstance(self.data, data.ALPACA_BTC_SCHEMA)
    positions = self.positionHub.getAllPositions()
    profitLossPerTick = []
    for pos in positions:
      # nun hier werden wir die Daten brauchen -> das Problem ist allerdings das
      # timestamps aufgerundet werden auf den jeweiligen nächsten tick
      # zudem können bei klines nur die open und close preise verwertet werden
      # eigentlich wären hier minütliche Datenpflicht
      # um jedoch einen ausreichenden Datenrahmen zu bekommen hätte man
      # die JSON verschiedener Responses zu konkatenieren.
      if not pos.isOpen:
        continue
      else:
        idx = pos.currentIdx
        if idx >= iterations:
          continue
        dataPoint = self.data.getDataAtIndex(idx)
        openPrice = dataPoint["o"]
        closePrice = dataPoint["c"]
        # for simplicity we use close price here
        entryPrice = openPrice
        currentPrice = closePrice
        variation = (currentPrice - entryPrice) * pos.amount
        profitLossPerTick.append(variation)
    self.variation = profitLossPerTick
    return profitLossPerTick
