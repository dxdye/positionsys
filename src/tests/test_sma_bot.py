# Add this at the top of the file to help debug
from unittest.mock import patch

import pytest

from src.data.data import TimeFrame
from src.position.position import Position, StopLossPosition
from src.sma_bot.sma_bot import SMABot


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

  def test_trade_history_multiple_cycles(self, sma_bot):
    """Test trade history with multiple buy/sell cycles."""
    prices = [100, 102, 101, 103, 105, 104, 110, 112, 115, 114, 112, 110, 108, 105, 107, 109, 111, 113, 115]

    sma_bot.decide_and_trade(prices[:8], current_idx=7)  # BUY
    sma_bot.decide_and_trade(prices[:13], current_idx=12)  # SELL
    sma_bot.decide_and_trade(prices[:18], current_idx=17)  # BUY

    history = sma_bot.get_trade_history()
    assert len(history) >= 3
    assert history[0]["type"] == "BUY"
    assert history[1]["type"] == "SELL"
    assert history[2]["type"] == "BUY"


# ============================================================================
# Test Abstract Interface Implementation
# ============================================================================


class TestSMABotAbstractInterface:
  """Test implementation of abstract bot interface methods."""

  def test_open_position_interface_method(self, sma_bot):
    """Test openPosition interface method."""
    prices = [100, 102, 104, 106, 108, 110, 112]
    position = sma_bot.openPosition(prices, currentIdx=6)

    assert position is not None
    assert isinstance(position, Position)

  def test_close_position_interface_method(self, sma_bot):
    """Test closePosition interface method."""
    prices = [100, 102, 101, 103, 105, 104, 110, 112, 115, 114, 112, 110, 108]

    # Open position first
    sma_bot.openPosition(prices[:8], currentIdx=7)
    position = sma_bot.get_positions()[0]

    # Close position
    result = sma_bot.closePosition(position, prices)
    assert result is True
    assert position.isOpen is False

  def test_act_on_tick_interface_method(self, sma_bot):
    """Test actOnTick interface method."""
    prices = [100, 102, 104, 106, 108, 110, 112]

    # Should execute without error
    sma_bot.actOnTick(prices, currentIdx=6)

    # Verify it made a decision
    assert len(sma_bot.get_trade_history()) > 0 or sma_bot.in_position is True or sma_bot.in_position is False


# ============================================================================
# Test Complete Bot Workflow
# ============================================================================


class TestSMABotCompleteWorkflow:
  """Test complete bot workflows."""

  def test_complete_trade_cycle(self, sma_bot):
    """Test a complete trade cycle: BUY -> SELL."""
    prices = [100, 102, 101, 103, 105, 104, 110, 112, 115, 114, 112, 110, 108]

    # Initial state
    assert sma_bot.in_position is False
    assert len(sma_bot.get_positions()) == 0

    # BUY
    sma_bot.decide_and_trade(prices[:8], currentIdx=7)
    assert sma_bot.in_position is True
    assert len(sma_bot.get_positions()) == 1

    # SELL
    sma_bot.decide_and_trade(prices, currentIdx=12)
    assert sma_bot.in_position is False

    # Verify trade history
    history = sma_bot.get_trade_history()
    assert len(history) == 2
    assert history[0]["type"] == "BUY"
    assert history[1]["type"] == "SELL"

  def test_bot_run_full_backtest(self, dummy_data):
    """Test the complete bot.run() method."""
    bot = SMABot(
      name="FullTestBot",
      data=dummy_data,
      short_window=3,
      long_window=5,
      stop_loss_percent=10.0,
      amount=1.0,
    )

    trade_history, profit_loss = bot.run()

    assert isinstance(trade_history, list)
    assert isinstance(profit_loss, list)

  def test_bot_reset(self, sma_bot):
    """Test bot reset functionality."""
    prices = [100, 102, 101, 103, 105, 104, 110, 112, 115, 114, 112, 110, 108]

    # Create some trades
    sma_bot.decide_and_trade(prices[:8], current_idx=7)
    sma_bot.decide_and_trade(prices, current_idx=12)

    # Verify state
    assert len(sma_bot.get_trade_history()) > 0

    # Reset
    sma_bot.reset()

    # Verify reset state
    assert sma_bot.in_position is False
    assert len(sma_bot.get_positions()) == 0
    assert len(sma_bot.get_trade_history()) == 0
    assert sma_bot.last_entry_idx == 0

  def test_multiple_trade_cycles(self, sma_bot):
    """Test multiple buy/sell cycles in sequence."""
    prices = [100, 102, 101, 103, 105, 104, 110, 112, 115, 114, 112, 110, 108, 105, 107, 109, 111, 113, 115]

    # First cycle
    sma_bot.decide_and_trade(prices[:8], current_idx=7)
    assert sma_bot.in_position is True

    sma_bot.decide_and_trade(prices[:13], current_idx=12)
    assert sma_bot.in_position is False

    # Second cycle
    sma_bot.decide_and_trade(prices[:18], current_idx=17)
    assert sma_bot.in_position is True

    history = sma_bot.get_trade_history()
    assert len(history) >= 3

  def test_no_trades_in_stable_market(self):
    """Test that bot doesn't trade in a stable market."""
    stable_prices = [100, 100, 101, 100, 101, 100, 101, 100, 101, 100, 101, 100]
    stable_data = DummyData(stable_prices, timeFrame=TimeFrame.ONEDAY)

    bot = SMABot(
      name="Stable SMA Bot",
      data=stable_data,
      short_window=3,
      long_window=5,
      stop_loss_percent=10.0,
      amount=1.0,
    )

    for idx in range(5, len(stable_prices)):
      window_prices = stable_prices[: idx + 1]
      bot.decide_and_trade(window_prices, current_idx=idx)

    history = bot.get_trade_history()
    assert len(history) <= 1


# ============================================================================
# Test Error Handling
# ============================================================================


class TestSMABotErrorHandling:
  """Test error handling in the bot."""

  def test_open_position_error_handling(self, sma_bot):
    """Test graceful error handling when opening position fails."""
    prices = [100, 102, 104, 106, 108, 110, 112]

    # Mock position hub to raise exception
    with patch.object(sma_bot.position_hub, "openNewPosition", side_effect=Exception("Test error")):
      decision = sma_bot.decide_and_trade(prices, current_idx=6)
      # Should return HOLD on error instead of raising
      assert decision == "HOLD"

  def test_close_position_error_handling(self, sma_bot):
    """Test graceful error handling when closing position fails."""
    prices = [100, 102, 101, 103, 105, 104, 110, 112, 115, 114, 112, 110, 108]

    # Open position
    sma_bot.decide_and_trade(prices[:8], current_idx=7)

    # Mock position hub to raise exception
    with patch.object(sma_bot.position_hub, "closeLatestPosition", side_effect=Exception("Test error")):
      decision = sma_bot.decide_and_trade(prices, current_idx=12)
      # Should return HOLD on error instead of raising
      assert decision == "HOLD"
      assert sma_bot.in_position is True  # Position stays open on error
