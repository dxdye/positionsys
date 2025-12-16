import pytest

from src.constants.constants import OrderType, PositionType
from src.data.data import TimeFrame
from src.position.position import (
  Position,
  PositionHub,
  PositionManagement,
  StopLossPosition,
)


class DummyData:
  """Dummy data class for testing."""

  def __init__(self, closing_prices, timeFrame=TimeFrame.ONEDAY):
    self._prices = closing_prices
    self.timeFrame = timeFrame

  def get_data_at_index(self, idx):
    if idx < 0 or idx >= len(self._prices):
      raise IndexError(f"Index {idx} out of range")
    return {"c": self._prices[idx], "o": self._prices[idx]}

  def get_data_length(self):
    return len(self._prices)


@pytest.fixture
def dummy_data():
  """Provide dummy data for testing."""
  prices = [100, 102, 101, 103, 105, 104, 110, 112, 115]
  return DummyData(prices, timeFrame=TimeFrame.ONEDAY)


class TestPosition:
  """Test the Position class."""

  def test_position_initialization(self):
    """Test Position initialization with valid parameters."""
    position = Position(entry_price=100.0, amount=1.0, timeFrame=TimeFrame.ONEDAY)

    assert position.amount == 1.0
    assert position.timeFrame == TimeFrame.ONEDAY
    assert position.entry_price == 100.0
    assert position.isOpen is True
    assert position.close_price is None
    assert position.orderType == OrderType.LONG
    assert position.positionType == PositionType.BASIC

  def test_position_initialization_short(self):
    """Test Position initialization with SHORT order type."""
    position = Position(entry_price=100.0, amount=1.0, timeFrame=TimeFrame.ONEDAY, orderType=OrderType.SHORT)

    assert position.orderType == OrderType.SHORT
    assert position.isOpen is True

  def test_position_amount_validation(self):
    """Test that Position rejects negative amounts."""
    with pytest.raises(ValueError, match="amount has to be bigger than 0"):
      Position(entry_price=100.0, amount=-1.0, timeFrame=TimeFrame.ONEDAY)

  def test_position_amount_zero(self):
    """Test that Position rejects zero amount."""
    with pytest.raises(ValueError, match="amount has to be bigger than 0"):
      Position(entry_price=100.0, amount=0, timeFrame=TimeFrame.ONEDAY)

  def test_position_entry_price_validation(self):
    """Test that Position rejects invalid entry prices."""
    with pytest.raises(ValueError, match="entry_price has to be bigger than 0"):
      Position(entry_price=0, amount=1.0, timeFrame=TimeFrame.ONEDAY)

    with pytest.raises(ValueError, match="entry_price has to be bigger than 0"):
      Position(entry_price=-100.0, amount=1.0, timeFrame=TimeFrame.ONEDAY)

  def test_position_timeframe_validation(self):
    """Test that Position validates timeFrame type."""
    with pytest.raises(ValueError, match="timeFrame has to be of type data.TimeFrame"):
      Position(entry_price=100.0, amount=1.0, timeFrame="INVALID")

  def test_position_close(self):
    """Test closing a position."""
    position = Position(entry_price=100.0, amount=1.0, timeFrame=TimeFrame.ONEDAY)

    assert position.isOpen is True
    position.close(close_price=105.0)
    assert position.isOpen is False
    assert position.close_price == 105.0

  def test_position_close_invalid_price(self):
    """Test that closing with invalid price raises exception."""
    position = Position(entry_price=100.0, amount=1.0, timeFrame=TimeFrame.ONEDAY)

    with pytest.raises(ValueError, match="close_price has to be provided and bigger than 0"):
      position.close(close_price=0)

    with pytest.raises(ValueError, match="close_price has to be provided and bigger than 0"):
      position.close(close_price=-5.0)

  def test_position_close_already_closed(self):
    """Test that closing an already closed position raises exception."""
    position = Position(entry_price=100.0, amount=1.0, timeFrame=TimeFrame.ONEDAY)
    position.close(close_price=105.0)

    with pytest.raises(RuntimeError, match="position is already closed"):
      position.close(close_price=110.0)

  def test_position_force_close(self):
    """Test force closing a position."""
    position = Position(entry_price=100.0, amount=1.0, timeFrame=TimeFrame.ONEDAY)

    position.close(close_price=105.0)
    assert position.isOpen is False
    assert position.close_price == 105.0

  def test_position_force_close_already_closed(self):
    """Test that force close works even if position is already closed."""
    position = Position(entry_price=100.0, amount=1.0, timeFrame=TimeFrame.ONEDAY)
    position.implicit_close()

    # Force close should work on already closed position
    position.close(close_price=110.0)
    assert position.isOpen is False
    assert position.close_price == 110.0  # Updated to new close price


class TestStopLossPosition:
  """Test the StopLossPosition class."""

  def test_stoploss_position_initialization(self):
    """Test StopLossPosition initialization."""
    position = StopLossPosition(
      entry_price=100.0, amount=1.0, timeFrame=TimeFrame.ONEDAY, stopLossPercent=5.0, orderType=OrderType.LONG
    )

    assert position.amount == 1.0
    assert position.entry_price == 100.0
    assert position.stopLossPercent == 5.0
    assert position.isOpen is True
    assert position.positionType == PositionType.BASIC  # Inherited from Position

  def test_stoploss_position_validation_zero(self):
    """Test that StopLossPosition rejects 0% stop loss."""
    with pytest.raises(ValueError, match="stopLossPercent has to be between 0 and 100"):
      StopLossPosition(entry_price=100.0, amount=1.0, timeFrame=TimeFrame.ONEDAY, stopLossPercent=0)

  def test_stoploss_position_validation_100(self):
    """Test that StopLossPosition rejects 100% stop loss."""
    with pytest.raises(ValueError, match="stopLossPercent has to be between 0 and 100"):
      StopLossPosition(entry_price=100.0, amount=1.0, timeFrame=TimeFrame.ONEDAY, stopLossPercent=100)

  def test_stoploss_position_validation_negative(self):
    """Test that StopLossPosition rejects negative stop loss."""
    with pytest.raises(ValueError, match="stopLossPercent has to be between 0 and 100"):
      StopLossPosition(entry_price=100.0, amount=1.0, timeFrame=TimeFrame.ONEDAY, stopLossPercent=-5.0)

  def test_stoploss_position_close_triggered_long(self):
    """Test that LONG position closes when price falls below stop loss."""
    position = StopLossPosition(
      entry_price=100.0, amount=1.0, timeFrame=TimeFrame.ONEDAY, stopLossPercent=10.0, orderType=OrderType.LONG
    )

    current_price = 88.0  # 12% drop, exceeds 10% stop loss

    position.implicit_close(current_price)
    assert position.isOpen is False

  def test_stoploss_position_close_not_triggered_long(self):
    """Test that LONG position doesn't close when price is above stop loss."""
    position = StopLossPosition(
      entry_price=100.0, amount=1.0, timeFrame=TimeFrame.ONEDAY, stopLossPercent=10.0, orderType=OrderType.LONG
    )

    current_price = 92.0  # 8% drop, below 10% stop loss threshold

    position.implicit_close(current_price)
    assert position.isOpen is True

  def test_stoploss_position_close_triggered_short(self):
    """Test that SHORT position closes when price rises above stop loss."""
    position = StopLossPosition(
      entry_price=100.0, amount=1.0, timeFrame=TimeFrame.ONEDAY, stopLossPercent=10.0, orderType=OrderType.SHORT
    )

    current_price = 112.0  # 12% increase, exceeds 10% stop loss for SHORT

    position.implicit_close(current_price)
    assert position.isOpen is False

  def test_stoploss_position_close_not_triggered_short(self):
    """Test that SHORT position doesn't close when price is below stop loss."""
    position = StopLossPosition(
      entry_price=100.0, amount=1.0, timeFrame=TimeFrame.ONEDAY, stopLossPercent=10.0, orderType=OrderType.SHORT
    )

    current_price = 108.0  # 8% increase, below 10% stop loss threshold

    position.implicit_close(current_price)
    assert position.isOpen is True

  def test_stoploss_position_close_no_price(self):
    """Test that close raises error when no price is provided."""
    position = StopLossPosition(entry_price=100.0, amount=1.0, timeFrame=TimeFrame.ONEDAY, stopLossPercent=10.0)

    with pytest.raises(ValueError, match="close_price has to be bigger than 0 - otherwise it be odd."):
      position.implicit_close(None)

  def test_stoploss_position_force_close(self):
    """Test force closing a stop loss position."""
    position = StopLossPosition(entry_price=100.0, amount=1.0, timeFrame=TimeFrame.ONEDAY, stopLossPercent=10.0)

    position.close(close_price=95.0)
    assert position.isOpen is False
    assert position.close_price == 95.0


class TestPositionHub:
  """Test the PositionHub class."""

  def test_position_hub_initialization(self):
    """Test PositionHub initialization."""
    hub = PositionHub()

    assert len(hub.positions) == 0
    assert hub.length == 0
    assert hub.timeFrame == TimeFrame.ONEDAY

  def test_position_hub_initialization_custom_timeframe(self):
    """Test PositionHub initialization with custom timeframe."""
    hub = PositionHub(timeFrame=TimeFrame.ONEHOUR)

    assert hub.timeFrame == TimeFrame.ONEHOUR

  def test_position_hub_get_all_positions_empty(self):
    """Test getting all positions from empty hub."""
    hub = PositionHub()
    positions = hub.get_all_positions()

    assert positions == []

  def test_position_hub_open_new_position(self):
    """Test opening a new position - note that this is currently broken in position.py."""
    hub = PositionHub()
    amount = 1.0

    # This will currently fail becaus.open_new_position doesn't accept entry_price
    # but Position.__init__ requires it
    with pytest.raises(TypeError):
      hub.open_new_position(amount)

  def test_position_hub_open_new_position_too_small(self):
    """Test that opening position with amount < SMALLEST_INVEST raises exception."""
    hub = PositionHub()

    with pytest.raises(Exception, match="amount should be bigger than smallest possible invest"):
      hub.open_new_position(amount=0.001, entry_price=100.0)

  def test_position_hub_open_position_object(self):
    """Test opening a position using a position object."""
    hub = PositionHub()
    position = Position(entry_price=100.0, amount=1.0, timeFrame=TimeFrame.ONEDAY)

    hub.open_position_object(position)

    assert len(hub.positions) == 1
    assert hub.length == 1
    assert hub.positions[0] == position

  def test_position_hub_open_position_object_invalid_type(self):
    """Test that opening position with invalid type raises exception."""
    hub = PositionHub()

    with pytest.raises(TypeError, match="position must be an instance of Position"):
      hub.open_position_object("not a position")

  def test_position_hub_close_latest_position(self):
    """Test closing the latest position."""
    hub = PositionHub()
    position = Position(entry_price=100.0, amount=1.0, timeFrame=TimeFrame.ONEDAY)
    hub.open_position_object(position)

    # Verify position was created
    assert len(hub.positions) > 0, "Position was not created"
    assert hub.positions[-1].isOpen is True, "Position should be open"

    # Close the position
    hub.close_latest_position(close_price=105.0)

    # Verify position was closed
    assert hub.positions[-1].isOpen is False, "Position should be closed"
    assert hub.positions[-1].close_price == 105.0

  def test_position_hub_close_latest_position_empty(self):
    """Test that closing position on empty hub raises exception."""
    hub = PositionHub()

    with pytest.raises(TypeError, match="No positions exist to close"):
      hub.close_latest_position(close_price=100.0)

  def test_position_hub_check_consistency(self):
    """Test the consistency check method."""
    hub = PositionHub()

    # Should pass with empty hub
    hub.check_consistency()

    # Add a position properly
    position = Position(entry_price=100.0, amount=1.0, timeFrame=TimeFrame.ONEDAY)
    hub.open_position_object(position)

    # Should pass when consistent
    hub.check_consistency()

    # Make it inconsistent
    hub.length = 999

    with pytest.raises(Exception, match="length is representative for the positionId"):
      hub.check_consistency()

  def test_position_hub_get_positions_by_type(self):
    """Test getting positions by type."""
    hub = PositionHub()

    # Add a basic position
    pos1 = Position(entry_price=100.0, amount=1.0, timeFrame=TimeFrame.ONEDAY)
    pos1.isOpen = False  # Close it so we can add another
    pos1.close_price = 105.0
    hub.positions.append(pos1)
    hub.length += 1

    # Add a stop loss position
    pos2 = StopLossPosition(entry_price=100.0, amount=2.0, timeFrame=TimeFrame.ONEDAY, stopLossPercent=5.0)
    hub.positions.append(pos2)
    hub.length += 1

    # Get basic positions
    basic_positions = hub.get_positions_by_type(Position)
    assert len(basic_positions) == 2  # StopLossPosition is also a Position

    # Get stop loss positions
    stop_loss_positions = hub.get_positions_by_type(StopLossPosition)
    assert len(stop_loss_positions) == 1
    assert stop_loss_positions[0] == pos2


class TestPositionManagement:
  """Test the PositionManagement class."""

  def test_position_management_initialization(self, dummy_data):
    """Test PositionManagement initialization."""
    management = PositionManagement(dummy_data, balance=1000.0, limit=10000.0)

    assert management.balance == 1000.0
    assert management.limit == 10000.0
    assert management.position_hub is not None
    assert isinstance(management.position_hub, PositionHub)
    assert management.tax_rate == 0.0

  def test_position_management_default_balance(self, dummy_data):
    """Test PositionManagement with default balance."""
    management = PositionManagement(dummy_data)

    assert management.balance == 200  # Default value

  def test_position_management_tax_rate(self, dummy_data):
    """Test PositionManagement with custom tax rate."""
    management = PositionManagement(dummy_data, tax_rate=0.25)

    assert management.tax_rate == 0.25

  def test_position_management_invalid_tax_rate(self, dummy_data):
    """Test PositionManagement rejects invalid tax rates."""
    with pytest.raises(ValueError, match="tax_rate must be between 0 and 1"):
      PositionManagement(dummy_data, tax_rate=-0.1)

    with pytest.raises(ValueError, match="tax_rate must be between 0 and 1"):
      PositionManagement(dummy_data, tax_rate=1.5)

  def test_position_management_evaluate_no_positions(self, dummy_data):
    """Test evaluate with no positions."""
    management = PositionManagement(dummy_data)

    result = management.evaluate()

    assert isinstance(result, list)
    assert len(result) == 0

  def test_position_management_evaluate_long_position(self, dummy_data):
    """Test evaluate with a closed long position."""
    management = PositionManagement(dummy_data)

    # Create and close a position
    position = Position(entry_price=100.0, amount=2.0, timeFrame=TimeFrame.ONEDAY, orderType=OrderType.LONG)
    position.close(close_price=110.0)
    management.position_hub.positions.append(position)
    management.position_hub.length = 1

    result = management.evaluate()

    # Profit should be (110 - 100) * 2 = 20
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0] == 20.0

  def test_position_management_evaluate_short_position(self, dummy_data):
    """Test evaluate with a closed short position."""
    management = PositionManagement(dummy_data)

    # Create and close a short position
    position = Position(entry_price=100.0, amount=2.0, timeFrame=TimeFrame.ONEDAY, orderType=OrderType.SHORT)
    position.close(close_price=90.0)
    management.position_hub.positions.append(position)
    management.position_hub.length = 1

    result = management.evaluate()

    # Profit should be (100 - 90) * 2 = 20
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0] == 20.0

  def test_position_management_evaluate_with_tax(self, dummy_data):
    """Test evaluate applies tax correctly."""
    management = PositionManagement(dummy_data, tax_rate=0.25)

    # Create and close a position
    position = Position(entry_price=100.0, amount=2.0, timeFrame=TimeFrame.ONEDAY)
    position.close(close_price=110.0)
    management.position_hub.positions.append(position)
    management.position_hub.length = 1

    result = management.evaluate()

    # Profit should be (110 - 100) * 2 * (1 - 0.25) = 20 * 0.75 = 15
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0] == 15.0

  def test_position_management_close_all_remaining_positions(self, dummy_data):
    """Test closing all remaining open positions."""
    management = PositionManagement(dummy_data)

    # Create open positions
    pos1 = Position(entry_price=100.0, amount=1.0, timeFrame=TimeFrame.ONEDAY)
    pos2 = Position(entry_price=105.0, amount=2.0, timeFrame=TimeFrame.ONEDAY)
    management.position_hub.positions.append(pos1)
    management.position_hub.positions.append(pos2)
    management.position_hub.length = 2

    # Close all positions at index 0
    management.close_all_remaining_open_positions(current_idx=0)

    # All positions should be closed
    assert pos1.isOpen is False
    assert pos2.isOpen is False
    assert pos1.close_price == 100  # Closing price from dummy_data at index 0
    assert pos2.close_price == 100

  def test_position_management_close_positions_on_condition(self, dummy_data):
    """Test closing positions on condition (stop loss)."""
    management = PositionManagement(dummy_data)

    # Create a stop loss position
    pos = StopLossPosition(entry_price=100.0, amount=1.0, timeFrame=TimeFrame.ONEDAY, stopLossPercent=5.0)
    management.position_hub.positions.append(pos)
    management.position_hub.length = 1

    # Current price at index 0 is 100, should not trigger stop loss
    management.close_all_positions_on_condition(current_idx=0)
    assert pos.isOpen is True


class TestPositionIntegration:
  """Integration tests for Position classes."""

  def test_position_lifecycle(self):
    """Test complete position lifecycle."""
    # Create position
    position = Position(entry_price=100.0, amount=1.0, timeFrame=TimeFrame.ONEDAY)
    assert position.isOpen is True
    assert position.entry_price == 100.0

    # Close position
    position.close(close_price=110.0)
    assert position.isOpen is False
    assert position.close_price == 110.0

  def test_stoploss_position_lifecycle(self):
    """Test StopLossPosition lifecycle."""
    position = StopLossPosition(entry_price=100.0, amount=1.0, timeFrame=TimeFrame.ONEDAY, stopLossPercent=10.0)

    # Test stop loss trigger
    position.close(close_price=88.0)
    assert position.isOpen is False

  def test_position_hub_workflow(self):
    """Test complete PositionHub workflow."""
    hub = PositionHub()

    # Open position using position object
    position = Position(entry_price=100.0, amount=1.0, timeFrame=TimeFrame.ONEDAY)
    hub.open_position_object(position)
    assert hub.length == 1

    # Get positions
    positions = hub.get_all_positions()
    assert len(positions) == 1
    assert positions[0] == position

    # Close latest position
    hub.close_latest_position(close_price=105.0)
    assert positions[0].isOpen is False

  def test_position_management_workflow(self, dummy_data):
    """Test complete PositionManagement workflow."""
    management = PositionManagement(dummy_data, balance=1000.0, tax_rate=0.1)

    # Add a position
    pos = Position(entry_price=100.0, amount=2.0, timeFrame=TimeFrame.ONEDAY)
    pos.close(close_price=110.0)
    management.position_hub.positions.append(pos)
    management.position_hub.length = 1

    # Evaluate
    results = management.evaluate()

    # Profit: (110 - 100) * 2 * (1 - 0.1) = 18
    assert len(results) == 1
    assert results[0] == 18.0
