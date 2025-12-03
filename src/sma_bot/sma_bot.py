import src.bot.bot as bot
from src.data import data as data_mod
from src.position.position import PositionHub, PositionSimulation, StopLossPosition

# ...rest of the code...


class SMABot(bot.bot):
  def __init__(self, name, data, short_window=40, long_window=100, stop_loss_percent=5.0, amount=1.0):
    """
    Initialize the SMABot.
    :param name: Name of the bot.
    :param data: Data object with timeFrame and price data.
    :param short_window: Window size for short-term SMA.
    :param long_window: Window size for long-term SMA.
    :param stop_loss_percent: Stop-loss percentage for positions.
    :param amount: Amount to invest per position.
    """
    super().__init__(name)
    self.position_hub = PositionHub()
    self.simulation = PositionSimulation(data)
    self.short_window = short_window
    self.long_window = long_window
    self.stop_loss_percent = stop_loss_percent
    self.amount = amount
    self.in_position = False
    self.last_entry_idx = 0
    self.timeFrame = data.timeFrame if hasattr(data, "timeFrame") else None
    self.trade_history = []

  def calculate_sma(self, prices, window):
    """
    Calculate the simple moving average.
    :param prices: List of prices.
    :param window: Window size for SMA.
    :return: SMA value or None if not enough data.
    """
    if len(prices) < window:
      return None
    return sum(prices[-window:]) / window

  def decide_and_trade(self, prices, current_idx):
    """
    Decide whether to buy or sell based on SMA crossover.
    :param prices: List of closing prices up to current index.
    :param current_idx: Current index in the data.
    :return: "BUY", "SELL", or "HOLD".
    """
    short_sma = self.calculate_sma(prices, self.short_window)
    long_sma = self.calculate_sma(prices, self.long_window)

    if short_sma is None or long_sma is None:
      return "HOLD"

    # Buy signal: short SMA crosses above long SMA
    if not self.in_position and short_sma > long_sma:
      try:
        pos = StopLossPosition(
          amount=self.amount, timeFrame=self.timeFrame, stopLossPercent=self.stop_loss_percent, currentIdx=current_idx
        )
        self.position_hub.positions.append(pos)
        self.position_hub.length += 1
        self.in_position = True
        self.last_entry_idx = current_idx
        self.trade_history.append({"type": "BUY", "idx": current_idx, "price": prices[-1]})
        return "BUY"
      except Exception as e:
        print(f"Error opening position: {e}")
        return "HOLD"

    # Sell signal: short SMA crosses below long SMA
    elif self.in_position and short_sma < long_sma:
      try:
        self.position_hub.closeLatestPosition()
        self.in_position = False
        self.trade_history.append({"type": "SELL", "idx": current_idx, "price": prices[-1]})
        return "SELL"
      except Exception as e:
        print(f"Error closing position: {e}")
        return "HOLD"

    return "HOLD"

  def run(self):
    """
    Run the bot through all data points and execute trades.
    :return: Trade history and final positions.
    """
    closing_prices = [self.simulation.data.getDataAtIndex(i)["c"] for i in range(self.simulation.data.getDataLength())]

    for idx in range(self.long_window, len(closing_prices)):
      window_prices = closing_prices[: idx + 1]
      decision = self.decide_and_trade(window_prices, idx)
      print(f"Tick {idx}: {decision} | Price: {closing_prices[idx]:.2f}")

    # Evaluate profit/loss
    profit_loss = self.simulation.reevaluate()
    return self.trade_history, profit_loss

  def get_positions(self):
    """
    Get all positions managed by the bot.
    :return: List of positions.
    """
    return self.position_hub.getAllPositions()

  def get_trade_history(self):
    """
    Get the bot's trade history.
    :return: List of trades executed.
    """
    return self.trade_history
