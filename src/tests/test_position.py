from datetime import datetime, timedelta

import pytest

from src.data.data import TimeFrame
from src.position.position import (
  Position,
  PositionHub,
  PositionSimulation,
  StopLossPosition,
  mapIndexToTime,
)


class DummyData:
  """Dummy data class for testing."""

  def __init__(self, closing_prices, timeFrame=TimeFrame.ONEDAY):
    self._prices = closing_prices
    self.timeFrame = timeFrame

  def getDataAtIndex(self, idx):
    if idx < 0 or idx >= len(self._prices):
      raise IndexError(f"Index {idx} out of range")
    return {"c": self._prices[idx], "o": self._prices[idx]}

  def getDataLength(self):
    return len(self._prices)


@pytest.fixture
def dummy_data():
  """Provide dummy data for testing."""
  prices = [100, 102, 101, 103, 105, 104, 110, 112, 115]
  return DummyData(prices, timeFrame=TimeFrame.ONEDAY)


class TestMapIndexToTime:
  """Test the mapIndexToTime function."""

  def test_map_index_to_time_oneday(self):
    """Test mapping index to time for ONEDAY timeframe."""
    now = datetime.now()
    time_mapped = mapIndexToTime(TimeFrame.ONEDAY, 0)

    # Should be today at 00:00:00
    assert time_mapped.hour == 0
    assert time_mapped.minute == 0
    assert time_mapped.second == 0

  def test_map_index_to_time_oneday_with_offset(self):
    """Test mapping with positive index offset."""
    now = datetime.now()
    time_mapped = mapIndexToTime(TimeFrame.ONEDAY, 1)
    time_mapped_zero = mapIndexToTime(TimeFrame.ONEDAY, 0)

    # Difference should be 1 day
    diff = time_mapped_zero - time_mapped
    assert diff.days == 1

  def test_map_index_to_time_onehour(self):
    """Test mapping index to time for ONEHOUR timeframe."""
    now = datetime.now()
    time_mapped = mapIndexToTime(TimeFrame.ONEHOUR, 0)

    # Should have minute and second set to 0
    assert time_mapped.minute == 0
    assert time_mapped.second == 0

  def test_map_index_to_time_oneminute(self):
    """Test mapping index to time for ONEMINUTE timeframe."""
    time_mapped = mapIndexToTime(TimeFrame.ONEMINUTE, 0)

    # Should have second and microsecond set to 0
    assert time_mapped.second == 0
    assert time_mapped.microsecond == 0

  def test_map_index_to_time_unsupported_timeframe(self):
    """Test that unsupported timeframe raises exception."""
    with pytest.raises(TypeError):
      mapIndexToTime("UNSUPPORTED", 0)


class TestPosition:
  """Test the Position class."""

  def test_position_initialization(self):
    """Test Position initialization with valid parameters."""
    position = Position(amount=1.0, timeFrame=TimeFrame.ONEDAY, currentIdx=0)

    assert position.amount == 1.0
    assert position.timeFrame == TimeFrame.ONEDAY
    assert position.currentIdx == 0
    assert position.isOpen is True
    assert position.closedAt is None
    assert position.createdAt is not None

  def test_position_amount_validation(self):
    """Test that Position rejects negative amounts."""
    with pytest.raises(ValueError, match="amount has to be bigger than 0"):
      Position(amount=-1.0, timeFrame=TimeFrame.ONEDAY, currentIdx=0)

  def test_position_amount_zero(self):
    """Test that Position rejects zero amount."""
    with pytest.raises(ValueError, match="amount has to be bigger than 0"):
      Position(amount=0, timeFrame=TimeFrame.ONEDAY, currentIdx=0)

  def test_position_timeframe_validation(self):
    """Test that Position validates timeFrame type."""
    with pytest.raises(ValueError, match="timeFrame has to be of type data.TimeFrame"):
      Position(amount=1.0, timeFrame="INVALID", currentIdx=0)

  def test_position_index_validation_negative(self):
    """Test that Position rejects negative index."""
    with pytest.raises(ValueError):
      Position(amount=1.0, timeFrame=TimeFrame.ONEDAY, currentIdx=-1)

  def test_position_index_validation_non_int(self):
    """Test that Position rejects non-integer index."""
    with pytest.raises(ValueError):
      Position(amount=1.0, timeFrame=TimeFrame.ONEDAY, currentIdx=1.5)

  def test_position_close(self):
    """Test closing a position."""
    position = Position(amount=1.0, timeFrame=TimeFrame.ONEDAY, currentIdx=0)

    assert position.isOpen is True
    position.close()
    assert position.isOpen is False
    assert position.closedAt is not None

  def test_position_close_already_closed(self):
    """Test that closing an already closed position raises exception."""
    position = Position(amount=1.0, timeFrame=TimeFrame.ONEDAY, currentIdx=0)
    position.close()

    with pytest.raises(TypeError):
      position.close()

  def test_position_force_close(self):
    """Test force closing a position."""
    position = Position(amount=1.0, timeFrame=TimeFrame.ONEDAY, currentIdx=0)

    position.forceClose()
    assert position.isOpen is False
    assert position.closedAt is not None

  def test_position_increment_idx(self):
    """Test incrementing the position index."""
    position = Position(amount=1.0, timeFrame=TimeFrame.ONEDAY, currentIdx=0)
    initial_idx = position.currentIdx

    position.incrementIdx()
    assert position.currentIdx == initial_idx + 1

  def test_position_create_dummy_position(self):
    """Test creating a dummy position for testing."""
    position = Position(amount=1.0, timeFrame=TimeFrame.ONEDAY, currentIdx=0)
    begin_time = datetime.now() - timedelta(days=5)
    close_time = datetime.now() - timedelta(days=1)

    position.createDummyPosition(begin_time, close_time, amount=5.0)

    assert position.createdAt == begin_time
    assert position.closedAt == close_time
    assert position.amount == 5.0


class TestStopLossPosition:
  """Test the StopLossPosition class."""

  def test_stoploss_position_initialization(self):
    """Test StopLossPosition initialization."""
    position = StopLossPosition(amount=1.0, timeFrame=TimeFrame.ONEDAY, stopLossPercent=5.0, currentIdx=0)

    assert position.amount == 1.0
    assert position.stopLossPercent == 5.0
    assert position.isOpen is True

  def test_stoploss_position_validation_zero(self):
    """Test that StopLossPosition rejects 0% stop loss."""
    with pytest.raises(ValueError, match="stopLossPercent has to be between 0 and 100"):
      StopLossPosition(amount=1.0, timeFrame=TimeFrame.ONEDAY, stopLossPercent=0, currentIdx=0)

  def test_stoploss_position_validation_100(self):
    """Test that StopLossPosition rejects 100% stop loss."""
    with pytest.raises(ValueError, match="stopLossPercent has to be between 0 and 100"):
      StopLossPosition(amount=1.0, timeFrame=TimeFrame.ONEDAY, stopLossPercent=100, currentIdx=0)

  def test_stoploss_position_validation_negative(self):
    """Test that StopLossPosition rejects negative stop loss."""
    with pytest.raises(ValueError, match="stopLossPercent has to be between 0 and 100"):
      StopLossPosition(amount=1.0, timeFrame=TimeFrame.ONEDAY, stopLossPercent=-5.0, currentIdx=0)

  def test_stoploss_position_close_triggered(self):
    """Test that position closes when price falls below stop loss."""
    position = StopLossPosition(amount=1.0, timeFrame=TimeFrame.ONEDAY, stopLossPercent=10.0, currentIdx=0)

    entry_price = 100.0
    current_price = 88.0  # 12% drop, exceeds 10% stop loss

    position.close(current_price, entry_price)
    assert position.isOpen is False

  def test_stoploss_position_close_not_triggered(self):
    """Test that position doesn't close when price is above stop loss."""
    position = StopLossPosition(amount=1.0, timeFrame=TimeFrame.ONEDAY, stopLossPercent=10.0, currentIdx=0)

    entry_price = 100.0
    current_price = 92.0  # 8% drop, below 10% stop loss threshold

    position.close(current_price, entry_price)
    assert position.isOpen is True


class TestPositionHub:
  """Test the PositionHub class."""

  def test_position_hub_initialization(self):
    """Test PositionHub initialization."""
    hub = PositionHub()

    assert len(hub.positions) == 0
    assert hub.length == 0

  def test_position_hub_get_all_positions_empty(self):
    """Test getting all positions from empty hub."""
    hub = PositionHub()
    positions = hub.getAllPositions()

    assert positions == []

  def test_position_hub_open_new_position(self):
    """Test opening a new position."""
    hub = PositionHub()
    amount = 1.0

    hub.openNewPosition(amount)

    assert len(hub.positions) == 1
    assert hub.length == 1

  def test_position_hub_open_new_position_too_small(self):
    """Test that opening position with amount < SMALLEST_INVEST raises exception."""
    hub = PositionHub()

    with pytest.raises(Exception, match="amount should be bigger than smallest possible invest"):
      hub.openNewPosition(0.001)

  def test_position_hub_close_latest_position(self):
    """Test closing the latest position."""
    hub = PositionHub()
    hub.openNewPosition(1.0)

    # Verify position was created
    assert len(hub.positions) > 0, "Position was not created"
    assert hub.positions[-1].isOpen is True, "Position should be open"

    # Close the position
    hub.closeLatestPosition()

    # Verify position was closed
    assert hub.positions[-1].isOpen is False, "Position should be closed"

  def test_position_hub_close_latest_position_empty(self):
    """Test that closing position on empty hub raises exception."""
    hub = PositionHub()

    with pytest.raises(TypeError, match="No positions exist to close"):
      hub.closeLatestPosition()


class TestPositionSimulation:
  """Test the PositionSimulation class."""

  def test_position_simulation_initialization(self, dummy_data):
    """Test PositionSimulation initialization."""
    simulation = PositionSimulation(dummy_data, balance=1000.0, limit=10000.0)

    assert simulation.balance == 1000.0
    assert simulation.limit == 10000.0
    assert simulation.positionHub is not None
    assert isinstance(simulation.positionHub, PositionHub)

  def test_position_simulation_default_balance(self, dummy_data):
    """Test PositionSimulation with default balance."""
    simulation = PositionSimulation(dummy_data)

    assert simulation.balance == 200  # Default value

  def test_position_simulation_reevaluate_no_positions(self, dummy_data):
    """Test reevaluate with no open positions."""
    simulation = PositionSimulation(dummy_data)

    result = simulation.reevaluate()

    assert isinstance(result, list)
    assert len(result) == 0

  def test_position_simulation_reevaluate_with_position(self, dummy_data):
    """Test reevaluate with an open position."""
    simulation = PositionSimulation(dummy_data)

    # Create a position manually
    position = Position(amount=1.0, timeFrame=TimeFrame.ONEDAY, currentIdx=0)
    simulation.positionHub.positions.append(position)
    simulation.positionHub.length = 1

    result = simulation.reevaluate()

    # Should calculate profit/loss for the position
    assert isinstance(result, list)


class TestPositionIntegration:
  """Integration tests for Position classes."""

  def test_position_lifecycle(self):
    """Test complete position lifecycle."""
    # Create position
    position = Position(amount=1.0, timeFrame=TimeFrame.ONEDAY, currentIdx=0)
    assert position.isOpen is True

    # Increment index
    position.incrementIdx()
    assert position.currentIdx == 1

    # Close position
    position.close()
    assert position.isOpen is False
    assert position.closedAt is not None

  def test_stoploss_position_lifecycle(self):
    """Test StopLossPosition lifecycle."""
    position = StopLossPosition(amount=1.0, timeFrame=TimeFrame.ONEDAY, stopLossPercent=10.0, currentIdx=0)

    # Test stop loss trigger
    position.close(currentPrice=88.0, entryPrice=100.0)
    assert position.isOpen is False
    assert position.currentIdx == 1  # Incremented

  def test_position_hub_workflow(self):
    """Test complete PositionHub workflow."""
    hub = PositionHub()

    # Open position
    hub.openNewPosition(1.0)
    assert hub.length == 1

    # Get positions
    positions = hub.getAllPositions()
    assert len(positions) > 0
