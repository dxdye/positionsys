from abc import abstractmethod

import position.position as position


class bot:  # trading bot interface
  def __init__(self, name):
    self.name = name

  @abstractmethod
  def closePosition(self, position: position.Position, priceData) -> bool:
    pass

  @abstractmethod
  def openPosition(self, priceData, currentIdx: int) -> position.Position | None:
    pass

  @abstractmethod
  def actOnTick(self, priceData, currentIdx: int) -> None:
    pass
