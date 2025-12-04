# Add this at the top of the file to help debug
from unittest.mock import patch

import pytest

from src.data.data import TimeFrame
from src.position.position import Position, StopLossPosition
from src.smabot.sma_bot import SMABot


class DummyData:
  """A minimal dummy data class to simulate real data for testing."""

  def __init__(self, closing_prices, timeFrame=TimeFrame.ONEDAY):
    self._prices = closing_prices
    self.timeFrame = timeFrame  # Ensure timeFrame is properly set

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
  return SMABot(
    name="TestBot",
    data=dummy_data,
    short_window=3,
    long_window=5,
    stop_loss_percent=10.0,
    amount=1.0,
  )


# ============================================================================
# Test Initialization and Configuration
# ============================================================================


class TestSMABotInitialization:
  """Tests for SMABot initialization and configuration."""

  def test_initialization_default_parameters(self, dummy_data):
    """Test bot initialization with default parameters."""
    bot = SMABot(name="TestBot", data=dummy_data)

    assert bot.name == "TestBot"
    assert bot.short_window == 40
    assert bot.long_window == 100
    assert bot.stop_loss_percent == 5.0
    assert bot.amount == 1.0
    assert bot.in_position is False
    assert bot.timeFrame == TimeFrame.ONEDAY
    assert len(bot.get_trade_history()) == 0
    assert len(bot.get_positions()) == 0

  def test_initialization_custom_parameters(self, dummy_data):
    """Test bot initialization with custom parameters."""
    bot = SMABot(
      name="CustomBot",
      data=dummy_data,
      short_window=20,
      long_window=50,
      stop_loss_percent=7.5,
      amount=2.5,
    )

    assert bot.short_window == 20
    assert bot.long_window == 50
    assert bot.stop_loss_percent == 7.5
    assert bot.amount == 2.5

  def test_initialization_invalid_window_sizes(self, dummy_data):
    """Test that initialization fails with invalid window sizes."""
    with pytest.raises(ValueError, match="short_window must be less than long_window"):
      SMABot(name="InvalidBot", data=dummy_data, short_window=100, long_window=50)

  def test_initialization_zero_window_size(self, dummy_data):
    """Test that initialization fails with zero window size."""
    with pytest.raises(ValueError, match="window sizes must be positive"):
      SMABot(name="InvalidBot", data=dummy_data, short_window=0, long_window=50)

  def test_initialization_negative_stop_loss(self, dummy_data):
    """Test that initialization fails with negative stop loss."""
    with pytest.raises(ValueError, match="stop_loss_percent must be positive"):
      SMABot(name="InvalidBot", data=dummy_data, stop_loss_percent=-5.0)

  def test_initialization_zero_amount(self, dummy_data):
    """Test that initialization fails with zero amount."""
    with pytest.raises(ValueError, match="amount must be positive"):
      SMABot(name="InvalidBot", data=dummy_data, amount=0)


# ============================================================================
# Test SMA Calculation
# ============================================================================


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

  def test_calculate_sma_empty_list(self, sma_bot):
    """Test SMA calculation with empty price list."""
    sma = sma_bot.calculate_sma([], window=3)
    assert sma is None

  def test_calculate_sma_window_of_one(self, sma_bot):
    """Test SMA calculation with window size of 1."""
    prices = [100, 102, 101, 103, 105]
    sma = sma_bot.calculate_sma(prices, window=1)
    assert sma == 105  # Last price

  def test_calculate_sma_uses_latest_prices(self, sma_bot):
    """Test that SMA uses the latest N prices, not first N."""
    prices = [100, 101, 102, 103, 104, 105, 106]
    sma = sma_bot.calculate_sma(prices, window=3)
    # Should be (104 + 105 + 106) / 3, not (100 + 101 + 102) / 3
    expected = (104 + 105 + 106) / 3
    assert sma == pytest.approx(expected)


# ============================================================================
# Test Trading Decisions
# ============================================================================


class TestSMABotTradingDecisions:
  """Test the trading decision logic."""

  def test_decide_and_trade_insufficient_data(self, sma_bot):
    """Test trading decision with insufficient data."""
    prices = [100, 101, 102]  # Only 3 prices, need at least 5 for long SMA
    decision = sma_bot.decide_and_trade(prices, current_idx=2)
    assert decision == "HOLD"

  def test_decide_and_trade_buy_signal(self, sma_bot):
    """Test BUY signal generation when short SMA > long SMA."""
    # Prices trending up: short SMA will be > long SMA
    prices = [100, 102, 104, 106, 108, 110, 112]
    decision = sma_bot.decide_and_trade(prices, current_idx=6)
    assert decision == "BUY"
    assert sma_bot.in_position is True
    assert len(sma_bot.get_positions()) == 1

  def test_decide_and_trade_no_second_buy_when_in_position(self, sma_bot):
    """Test that no second BUY is issued when already in position."""
    prices = [100, 102, 104, 106, 108, 110, 112, 114, 116]

    # First BUY
    sma_bot.decide_and_trade(prices[:7], current_idx=6)
    assert len(sma_bot.get_positions()) == 1

    # Try another BUY while in position (should be ignored)
    decision = sma_bot.decide_and_trade(prices, current_idx=8)
    assert decision == "HOLD"
    assert len(sma_bot.get_positions()) == 1

  def test_decide_and_trade_sell_signal(self, sma_bot):
    """Test SELL signal generation when short SMA < long SMA."""
    prices = [100, 102, 101, 103, 105, 104, 110, 112, 115, 114, 112, 110, 108]

    # BUY first
    sma_bot.decide_and_trade(prices[:8], current_idx=7)
    assert sma_bot.in_position is True

    # SELL
    decision = sma_bot.decide_and_trade(prices, current_idx=12)
    assert decision == "SELL"
    assert sma_bot.in_position is False

  def test_decide_and_trade_no_sell_when_not_in_position(self, sma_bot):
    """Test that SELL signal is not issued when not in position."""
    prices = [100, 102, 101, 103, 105, 104, 110, 112, 115, 114, 112, 110, 108]

    # Try SELL without being in position
    decision = sma_bot.decide_and_trade(prices, current_idx=12)
    assert decision == "HOLD"  # No signal because not in position
    assert sma_bot.in_position is False


# ============================================================================
# Test Position Management
# ============================================================================


class TestSMABotPositionManagement:
  """Test position opening and closing functionality."""

  def test_open_position_success(self, sma_bot):
    """Test successful position opening."""
    prices = [100, 102, 104, 106, 108, 110, 112]
    decision = sma_bot.decide_and_trade(prices, current_idx=6)

    assert decision == "BUY"
    assert sma_bot.in_position is True
    assert len(sma_bot.get_positions()) == 1

    position = sma_bot.get_positions()[0]
    assert isinstance(position, StopLossPosition)
    assert position.amount == 1.0
    assert position.stopLossPercent == 10.0
    assert position.isOpen is True

  def test_close_position_success(self, sma_bot):
    """Test successful position closing."""
    prices = [100, 102, 101, 103, 105, 104, 110, 112, 115, 114, 112, 110, 108]

    # Open position
    sma_bot.decide_and_trade(prices[:8], current_idx=7)
    position = sma_bot.get_positions()[0]
    assert position.isOpen is True

    # Close position
    sma_bot.decide_and_trade(prices, current_idx=12)
    assert position.isOpen is False
    assert sma_bot.in_position is False

  def test_get_positions_returns_all_positions(self, sma_bot):
    """Test that get_positions returns all managed positions."""
    prices = [100, 102, 101, 103, 105, 104, 110, 112, 115, 114, 112, 110, 108, 105, 107, 109, 111, 113, 115]

    # Multiple buy/sell cycles
    sma_bot.decide_and_trade(prices[:8], current_idx=7)
    sma_bot.decide_and_trade(prices[:13], current_idx=12)
    sma_bot.decide_and_trade(prices[:18], current_idx=17)

    positions = sma_bot.get_positions()
    assert len(positions) >= 2

  def test_get_open_positions_count(self, sma_bot):
    """Test getting count of open positions."""
    prices = [100, 102, 101, 103, 105, 104, 110, 112, 115, 114, 112, 110, 108]

    # No open positions initially
    assert sma_bot.get_open_positions_count() == 0

    # Open position
    sma_bot.decide_and_trade(prices[:8], current_idx=7)
    assert sma_bot.get_open_positions_count() == 1

    # Close position
    sma_bot.decide_and_trade(prices, current_idx=12)
    assert sma_bot.get_open_positions_count() == 0


# ============================================================================
# Test Trade History
# ============================================================================


class TestSMABotTradeHistory:
  """Test trade history tracking."""

  def test_trade_history_empty_initially(self, sma_bot):
    """Test that trade history is empty initially."""
    assert len(sma_bot.get_trade_history()) == 0

  def test_trade_history_buy_signal(self, sma_bot):
    """Test trade history records BUY signal."""
    prices = [100, 102, 104, 106, 108, 110, 112]
    sma_bot.decide_and_trade(prices, current_idx=6)

    history = sma_bot.get_trade_history()
    assert len(history) == 1
    assert history[0]["type"] == "BUY"
    assert history[0]["idx"] == 6
    assert history[0]["price"] == 112

  def test_trade_history_buy_and_sell(self, sma_bot):
    """Test trade history records both BUY and SELL."""
    prices = [100, 102, 101, 103, 105, 104, 110, 112, 115, 114, 112, 110, 108]

    sma_bot.decide_and_trade(prices[:8], current_idx=7)
    sma_bot.decide_and_trade(prices, current_idx=12)

    history = sma_bot.get_trade_history()
    assert len(history) == 2
    assert history[0]["type"] == "BUY"
    assert history[1]["type"] == "SELL"

  def test_trade_history_multiple_cycles(self):
    """Test trade history with multiple buy/sell cycles.

    This test creates its own data and bot to ensure consistent test data.
    """
    # Create specific price data for multiple cycles
    prices = [100, 102, 101, 103, 105, 104, 110, 112, 115, 114, 112, 110, 108, 105, 107, 109, 111, 113, 115]
    data = DummyData(prices, timeFrame=TimeFrame.ONEDAY)

    bot = SMABot(
      name="MultiCycleBot",
      data=data,
      short_window=3,
      long_window=5,
      stop_loss_percent=10.0,
      amount=1.0,
    )

    # Cycle 1: BUY
    result1 = bot.decide_and_trade(prices[:8], current_idx=7)
    assert result1 == "BUY"

    # Cycle 1: SELL
    result2 = bot.decide_and_trade(prices[:13], current_idx=12)
    assert result2 == "SELL"

    # Cycle 2: BUY
    result3 = bot.decide_and_trade(prices[:18], current_idx=17)
    assert result3 == "BUY"

    history = bot.get_trade_history()
    assert len(history) >= 3, f"Expected >= 3 trades, got {len(history)}"
    assert history[0]["type"] == "BUY"
    assert history[1]["type"] == "SELL"
    assert history[2]["type"] == "BUY"


# ============================================================================
# Test Abstract Interface Implementation
# ============================================================================


class TestSMABotAbstractInterface:
  """Test implementation of abstract bot interface methods."""


class TestSMABotCompleteWorkflow:
  """Test complete trading workflows including the run() method."""

  def test_bot_run_full_backtest(self):
    """
    Test complete backtest cycle using the run() method.

    This test verifies that:
    1. The bot can run through all data points
    2. Trades are executed correctly
    3. Trade history is recorded
    4. Profit/loss is calculated
    """
    # Create price data with clear trend: uptrend then downtrend
    prices = [100, 102, 104, 106, 108, 110, 112, 114, 116, 118, 120, 118, 116, 114, 112, 110, 108, 106, 104, 102, 100]
    data = DummyData(prices, timeFrame=TimeFrame.ONEDAY)

    bot = SMABot(
      name="BacktestBot",
      data=data,
      short_window=3,
      long_window=5,
      stop_loss_percent=5.0,
      amount=1.0,
    )

    # Run the backtest
    trade_history, profit_loss = bot.run()

    # Verify results
    assert isinstance(trade_history, list), "Trade history should be a list"
    assert isinstance(profit_loss, (int, float)), "Profit/loss should be a number"
    assert len(trade_history) > 0, "Should have at least one trade"

    # Verify trade history structure
    for trade in trade_history:
      assert "type" in trade, "Trade should have 'type' field"
      assert "idx" in trade, "Trade should have 'idx' field"
      assert "price" in trade, "Trade should have 'price' field"
      assert trade["type"] in ["BUY", "SELL"], "Trade type should be BUY or SELL"

    # Verify trades alternate between BUY and SELL
    for i, trade in enumerate(trade_history):
      if i > 0:
        prev_type = trade_history[i - 1]["type"]
        curr_type = trade["type"]
        # After BUY should come SELL, after SELL should come BUY
        if prev_type == "BUY":
          assert curr_type == "SELL", "SELL should follow BUY"
        elif prev_type == "SELL":
          assert curr_type == "BUY", "BUY should follow SELL"

  def test_bot_run_with_trending_market(self):
    """Test bot run() in a strong uptrend - should generate BUY signals."""
    # Clear uptrend: prices steadily increase
    prices = [100, 102, 104, 106, 108, 110, 112, 114, 116, 118, 120, 122, 124, 126, 128]
    data = DummyData(prices, timeFrame=TimeFrame.ONEDAY)

    bot = SMABot(
      name="UptrendBot",
      data=data,
      short_window=3,
      long_window=5,
      stop_loss_percent=5.0,
      amount=1.0,
    )

    trade_history, profit_loss = bot.run()

    # In uptrend, should have at least one BUY
    assert len(trade_history) >= 1
    assert any(trade["type"] == "BUY" for trade in trade_history)

  def test_bot_run_with_downtrend(self):
    """Test bot run() in a downtrend - should generate SELL signals after BUY."""
    # Downtrend: prices steadily decrease
    prices = [128, 126, 124, 122, 120, 118, 116, 114, 112, 110, 108, 106, 104, 102, 100]
    data = DummyData(prices, timeFrame=TimeFrame.ONEDAY)

    bot = SMABot(
      name="DowntrendBot",
      data=data,
      short_window=3,
      long_window=5,
      stop_loss_percent=5.0,
      amount=1.0,
    )

    trade_history, profit_loss = bot.run()

    # Downtrend should generate very few or no trades
    # (short SMA won't be > long SMA in sustained downtrend)
    assert len(trade_history) <= 2

  def test_bot_run_resets_state(self):
    """Test that running the bot multiple times requires reset."""
    prices = [100, 102, 104, 106, 108, 110, 112, 114, 116, 118, 120]
    data = DummyData(prices, timeFrame=TimeFrame.ONEDAY)

    bot = SMABot(
      name="ResetBot",
      data=data,
      short_window=3,
      long_window=5,
      stop_loss_percent=5.0,
      amount=1.0,
    )

    # Run once
    history1, profit1 = bot.run()
    initial_trades = len(history1)

    # Run again without reset - should have double the trades
    history2, profit2 = bot.run()
    assert len(history2) >= initial_trades, "Running twice should accumulate trades"

    # Reset and run again
    bot.reset()
    history3, profit3 = bot.run()
    assert len(history3) == initial_trades, "After reset, should have same trades as first run"

  def test_bot_run_empty_data(self):
    """Test bot run() with insufficient data."""
    # Not enough data for SMA calculation
    prices = [100, 101, 102]
    data = DummyData(prices, timeFrame=TimeFrame.ONEDAY)

    bot = SMABot(
      name="EmptyBot",
      data=data,
      short_window=3,
      long_window=5,
      stop_loss_percent=5.0,
      amount=1.0,
    )

    trade_history, profit_loss = bot.run()

    # Should not crash, but may have few or no trades
    assert isinstance(trade_history, list)
    assert isinstance(profit_loss, (int, float))

  def test_bot_run_trade_prices_match_data(self):
    """Test that recorded trade prices match the actual data at those indices."""
    prices = [100, 102, 104, 106, 108, 110, 112, 114, 116, 118, 120]
    data = DummyData(prices, timeFrame=TimeFrame.ONEDAY)

    bot = SMABot(
      name="PriceCheckBot",
      data=data,
      short_window=3,
      long_window=5,
      stop_loss_percent=5.0,
      amount=1.0,
    )

    trade_history, profit_loss = bot.run()

    # Verify each trade's price matches the data at that index
    for trade in trade_history:
      idx = trade["idx"]
      recorded_price = trade["price"]
      actual_price = prices[idx]
      assert recorded_price == actual_price, (
        f"Trade at index {idx} recorded price {recorded_price}, but actual was {actual_price}"
      )

  def test_bot_run_indices_are_valid(self):
    """Test that all trade indices are within valid range."""
    prices = [100, 102, 104, 106, 108, 110, 112, 114, 116, 118, 120]
    data = DummyData(prices, timeFrame=TimeFrame.ONEDAY)

    bot = SMABot(
      name="IndexCheckBot",
      data=data,
      short_window=3,
      long_window=5,
      stop_loss_percent=5.0,
      amount=1.0,
    )

    trade_history, profit_loss = bot.run()

    # All trade indices should be within the data range
    for trade in trade_history:
      idx = trade["idx"]
      assert 0 <= idx < len(prices), f"Trade index {idx} out of valid range [0, {len(prices) - 1}]"

  def test_bot_run_profit_loss_calculation(self):
    """Test that profit/loss is calculated after running the bot."""
    # Prices that go up then down - should result in loss if we bought high
    prices = [100, 102, 104, 106, 108, 110, 112, 110, 108, 106, 104, 102, 100]
    data = DummyData(prices, timeFrame=TimeFrame.ONEDAY)

    bot = SMABot(
      name="ProfitBot",
      data=data,
      short_window=3,
      long_window=5,
      stop_loss_percent=5.0,
      amount=1.0,
    )

    trade_history, profit_loss = bot.run()

    # The bot ran and calculated profit/loss
    assert isinstance(profit_loss, (int, float))
    # Profit/loss should be a reasonable number (not NaN or infinity)
    assert profit_loss == profit_loss  # NaN check (NaN != NaN)
    assert profit_loss != float("inf") and profit_loss != float("-inf")

  def test_bot_run_positions_consistency(self):
    """Test that positions are managed consistently during run."""
    prices = [100, 102, 104, 106, 108, 110, 112, 114, 116, 118, 120]
    data = DummyData(prices, timeFrame=TimeFrame.ONEDAY)

    bot = SMABot(
      name="PositionBot",
      data=data,
      short_window=3,
      long_window=5,
      stop_loss_percent=5.0,
      amount=1.0,
    )

    trade_history, profit_loss = bot.run()

    # After run, all positions should be properly closed
    positions = bot.get_positions()
    assert len(positions) > 0, "Should have created at least one position"

    # All but possibly the last position should be closed
    open_positions = [p for p in positions if p.isOpen]
    assert len(open_positions) <= 1, "Should have at most one open position after run"
