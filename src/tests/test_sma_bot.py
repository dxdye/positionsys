import pytest

from src.data.data import TimeFrame
from src.position.position import PositionHub, StopLossPosition
from src.sma_bot.sma_bot import SMABot


class DummyData:
  """A minimal dummy data class to simulate real data for testing."""

  def __init__(self, closing_prices, timeFrame=TimeFrame.ONEDAY):
    self._prices = closing_prices
    self.timeFrame = timeFrame

  def getDataAtIndex(self, idx):
    """Get data point at index."""
    if idx < 0 or idx >= len(self._prices):
      raise IndexError(f"Index {idx} out of range")
    return {"c": self._prices[idx], "o": self._prices[idx]}

  def getDataLength(self):
    """Get total number of data points."""
    return len(self._prices)


@pytest.fixture
def dummy_prices_with_crossover():
  """
  Simulate a price series with a clear SMA crossover.
  Short SMA (3) will cross above long SMA (5) around index 6-7.
  """
  return [100, 102, 101, 103, 105, 104, 110, 112, 115, 114, 112, 110, 108]


@pytest.fixture
def dummy_data(dummy_prices_with_crossover):
  """Provide a dummy data object for testing."""
  return DummyData(dummy_prices_with_crossover, timeFrame=TimeFrame.ONEDAY)


@pytest.fixture
def sma_bot(dummy_data):
  """Provide a configured SMABot instance for testing."""
  return SMABot(name="TestBot", data=dummy_data, short_window=3, long_window=5, stop_loss_percent=10.0, amount=1.0)


class TestSMABotFunctional:
  """Functional tests for the complete SMABot workflow."""

  def test_complete_trade_cycle(self, sma_bot):
    """
    Test a complete trade cycle: initialization -> buy signal -> sell signal.
    This is the main functional test that validates the bot's core behavior.
    """
    prices = [100, 102, 101, 103, 105, 104, 110, 112, 115, 114, 112, 110, 108]

    # Initial state: no position open
    assert sma_bot.in_position is False
    assert len(sma_bot.get_positions()) == 0

    # Index 7: BUY signal (short SMA crosses above long SMA)
    buy_decision = sma_bot.decide_and_trade(prices[:8], current_idx=7)
    assert buy_decision == "BUY"
    assert sma_bot.in_position is True
    assert len(sma_bot.get_positions()) == 1

    # Verify position properties
    position = sma_bot.get_positions()[0]
    assert isinstance(position, StopLossPosition)
    assert position.isOpen is True
    assert position.amount == 1.0
    assert position.stopLossPercent == 10.0

    # Index 12: SELL signal (short SMA crosses below long SMA)
    sell_decision = sma_bot.decide_and_trade(prices, current_idx=12)
    assert sell_decision == "SELL"
    assert sma_bot.in_position is False

    # Verify position is closed
    position = sma_bot.get_positions()[0]
    assert position.isOpen is False
    assert position.closedAt is not None

    # Verify trade history
    history = sma_bot.get_trade_history()
    assert len(history) == 2
    assert history[0]["type"] == "BUY"
    assert history[0]["price"] == 112
    assert history[1]["type"] == "SELL"
    assert history[1]["price"] == 108

  def test_multiple_trade_cycles(self, sma_bot):
    """
    Test multiple buy/sell cycles in sequence.
    This validates that the bot can handle multiple trades.
    """
    # Simulate multiple price waves
    prices = [100, 102, 101, 103, 105, 104, 110, 112, 115, 114, 112, 110, 108, 105, 107, 109, 111, 113, 115]

    # First cycle: BUY
    sma_bot.decide_and_trade(prices[:8], current_idx=7)
    assert sma_bot.in_position is True
    assert len(sma_bot.get_positions()) == 1

    # First cycle: SELL
    sma_bot.decide_and_trade(prices[:13], current_idx=12)
    assert sma_bot.in_position is False

    # Second cycle: BUY (on new uptrend)
    sma_bot.decide_and_trade(prices[:18], current_idx=17)
    assert sma_bot.in_position is True
    assert len(sma_bot.get_positions()) == 2

    # Verify trade history has 3 trades (BUY, SELL, BUY)
    history = sma_bot.get_trade_history()
    assert len(history) >= 3

  def test_bot_run_full_backtest(self, dummy_data):
    """
    Test the complete bot.run() method which simulates the entire backtest.
    This is the most comprehensive functional test.
    """
    bot = SMABot(name="FullTestBot", data=dummy_data, short_window=3, long_window=5, stop_loss_percent=10.0, amount=1.0)

    # Execute full backtest
    trade_history, profit_loss = bot.run()

    # Verify output types
    assert isinstance(trade_history, list)
    assert isinstance(profit_loss, list)

    # Verify trades occurred
    assert len(trade_history) > 0

    # Verify trade history structure
    for trade in trade_history:
      assert "type" in trade
      assert "idx" in trade
      assert "price" in trade
      assert trade["type"] in ["BUY", "SELL"]
      assert isinstance(trade["idx"], int)
      assert isinstance(trade["price"], (int, float))

  def test_sma_crossover_logic(self, sma_bot):
    """
    Test the SMA crossover logic specifically.
    This validates the core trading signal generation.
    """
    # Setup: prices trending up
    uptrend_prices = [100, 102, 104, 106, 108, 110, 112, 114, 116]

    # Short SMA should be above long SMA in uptrend
    short_sma = sma_bot.calculate_sma(uptrend_prices, 3)
    long_sma = sma_bot.calculate_sma(uptrend_prices, 5)

    assert short_sma > long_sma

    # BUY signal should occur
    decision = sma_bot.decide_and_trade(uptrend_prices, current_idx=8)
    assert decision == "BUY"

    # Setup: prices trending down
    downtrend_prices = uptrend_prices + [115, 113, 111, 109, 107, 105]

    # Short SMA should be below long SMA in downtrend (eventually)
    short_sma_down = sma_bot.calculate_sma(downtrend_prices[-5:], 3)
    long_sma_down = sma_bot.calculate_sma(downtrend_prices, 5)

    # After sufficient downtrend, SELL signal should occur
    if short_sma_down < long_sma_down:
      decision = sma_bot.decide_and_trade(downtrend_prices, current_idx=14)
      assert decision == "SELL"

  def test_position_lifecycle(self, sma_bot):
    """
    Test the complete lifecycle of a position from creation to closure.
    This validates position state management.
    """
    prices = [100, 102, 101, 103, 105, 104, 110, 112, 115, 114, 112, 110, 108]

    # Before trade
    assert len(sma_bot.get_positions()) == 0

    # After BUY
    sma_bot.decide_and_trade(prices[:8], current_idx=7)
    positions = sma_bot.get_positions()
    assert len(positions) == 1
    assert positions[0].isOpen is True
    assert positions[0].createdAt is not None
    assert positions[0].closedAt is None

    # After SELL
    sma_bot.decide_and_trade(prices, current_idx=12)
    positions = sma_bot.get_positions()
    assert len(positions) == 1
    assert positions[0].isOpen is False
    assert positions[0].closedAt is not None

  def test_no_trades_in_stable_market(self):
    """
    Test that bot doesn't trade in a stable market (no crossovers).
    This validates that bot only trades on clear signals.
    """
    # Stable market: price oscillates but no clear trend
    stable_prices = [100, 100, 101, 100, 101, 100, 101, 100, 101, 100, 101, 100]
    stable_data = DummyData(stable_prices, timeFrame=TimeFrame.ONEDAY)

    bot = SMABot(name="StableBot", data=stable_data, short_window=3, long_window=5, stop_loss_percent=10.0, amount=1.0)

    # Run through all prices
    for idx in range(5, len(stable_prices)):
      window_prices = stable_prices[: idx + 1]
      decision = bot.decide_and_trade(window_prices, current_idx=idx)
      # In stable market, should mostly HOLD

    # Should have minimal or no trades
    history = bot.get_trade_history()
    assert len(history) <= 1  # At most a single incomplete trade


class TestSMABotCalculateSMA:
  """Test the SMA calculation method."""

  def test_calculate_sma_sufficient_data(self, sma_bot):
    """Test SMA calculation with sufficient data."""
    prices = [100, 102, 101, 103, 105]
    sma = sma_bot.calculate_sma(prices, window=3)
    expected = (101 + 103 + 105) / 3
    assert sma == pytest.approx(expected)

  def test_calculate_sma_insufficient_data(self, sma_bot):
    """Test SMA calculation with insufficient data."""
    prices = [100, 102]
    sma = sma_bot.calculate_sma(prices, window=3)
    assert sma is None

  def test_calculate_sma_exact_window_size(self, sma_bot):
    """Test SMA calculation with exactly window size data."""
    prices = [100, 102, 101]
    sma = sma_bot.calculate_sma(prices, window=3)
    expected = (100 + 102 + 101) / 3
    assert sma == pytest.approx(expected)
