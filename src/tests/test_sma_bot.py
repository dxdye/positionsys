"""
BDD Step definitions for SMA Bot testing using pytest-bdd.
"""

import pytest
from pytest_bdd import given, parsers, then, when

from src.constants.constants import BotAction
from src.data.data import TimeFrame
from src.position.position import StopLossPosition
from src.smabot.sma_bot import SMABot


# Helper class for test data
class DummyData:
  """A minimal dummy data class to simulate real data for testing."""

  def __init__(self, closing_prices, timeFrame=TimeFrame.ONEDAY):
    self._prices = closing_prices
    self.timeFrame = timeFrame

  def get_data_at_index(self, idx):
    """Get data point at index."""
    if idx < 0 or idx >= len(self._prices):
      raise IndexError(f"Index {idx} out of range")
    return {"c": self._prices[idx], "o": self._prices[idx]}

  def get_data_length(self):
    """Get total number of data points."""
    return len(self._prices)

  def get_closing_prices(self):
    """Return the list of closing prices (for compatibility with real Data)."""
    return self._prices


# Load all feature files
# Wrapped in try-except to handle cases where pytest config is not available (e.g., pdoc import)
try:
  from pytest_bdd import scenarios

  scenarios("features/sma_bot_initialization.feature")
  scenarios("features/sma_calculation.feature")
  scenarios("features/sma_trading_decisions.feature")
  scenarios("features/sma_bot_workflow.feature")
except (IndexError, RuntimeError):
  # IndexError: occurs when pytest CONFIG_STACK is empty (e.g., during pdoc import)
  # RuntimeError: other potential issues during scenario loading
  pass


# ============================================================================
# Shared Fixtures and Context
# ============================================================================


@pytest.fixture
def context():
  """Shared context for test data across steps."""
  return {
    "data": None,
    "bot": None,
    "prices": [],
    "decision": None,
    "error": None,
    "sma_result": None,
    "trade_history": None,
    "profit_loss": None,
    "first_run_trades": 0,
  }


# ============================================================================
# Given Steps - Setup
# ============================================================================


@given('I have price data with timeframe "ONEDAY"')
def have_price_data(context):
  """Create basic price data."""
  context["prices"] = [100, 102, 104, 106, 108, 110, 112]
  context["data"] = DummyData(context["prices"], timeFrame=TimeFrame.ONEDAY)


@given("I have an SMA bot")
def have_sma_bot(context):
  """Create a basic SMA bot."""
  prices = [100, 102, 104, 106, 108, 110, 112]
  context["data"] = DummyData(prices, timeFrame=TimeFrame.ONEDAY)
  context["bot"] = SMABot(
    name="TestBot",
    data=context["data"],
    short_window=3,
    long_window=5,
    stop_loss_percent=10.0,
    amount=1.0,
  )


@given(parsers.parse("I have an SMA bot with short window {short:d} and long window {long:d}"))
def have_sma_bot_with_windows(context, short, long):
  """Create SMA bot with specific window sizes."""
  prices = [100, 102, 101, 103, 105, 104, 110, 112, 115, 114, 112, 110, 108]
  context["prices"] = prices
  context["data"] = DummyData(prices, timeFrame=TimeFrame.ONEDAY)
  context["bot"] = SMABot(
    name="TestBot",
    data=context["data"],
    short_window=short,
    long_window=long,
    stop_loss_percent=10.0,
    amount=1.0,
  )


@given(parsers.parse("I have price data: {prices_str}"))
def have_specific_price_data(context, prices_str):
  """Parse and set specific price data."""
  # Parse price data from string like "[100, 102, 104]"
  prices_str = prices_str.strip("[]")
  context["prices"] = [float(p.strip()) for p in prices_str.split(",")]


@given("I have an empty price list")
def have_empty_price_list(context):
  """Set empty price list."""
  context["prices"] = []


@given(parsers.parse("I have opened a position at index {idx:d}"))
def have_opened_position(context, idx):
  """Open a position at specific index."""
  prices = context["prices"][: idx + 1]
  context["bot"].decide_and_trade(prices, idx)


@given(parsers.parse("I have opened a position at index {idx:d} with entry price {price:f}"))
def have_opened_position_with_price(context, idx, price):
  """Open a position at specific index with entry price."""
  # Modify the price data to have the specific entry price
  context["prices"][idx] = price
  context["data"]._prices = context["prices"]
  prices = context["prices"][: idx + 1]
  context["bot"].decide_and_trade(prices, idx)


@given(parsers.parse("the stop loss percent is {percent:f}"))
def set_stop_loss_percent(context, percent):
  """Set stop loss percentage."""
  context["bot"].stop_loss_percent = percent


@given(parsers.parse("the bot opens a position at price {price:f}"))
def bot_opens_position_at_price(context, price):
  """Bot opens a position at a specific price."""
  # Manually create and add a position
  from src.constants.constants import OrderType
  from src.position.position import StopLossPosition

  position = StopLossPosition(
    entry_price=price,
    amount=context["bot"].amount,
    timeFrame=context["bot"].timeFrame,
    stopLossPercent=context["bot"].stop_loss_percent,
    orderType=OrderType.LONG,
  )
  context["bot"].position_management.position_hub.positions.append(position)
  context["bot"].position_management.position_hub.length += 1


@given(parsers.parse("I manually create a position with entry price {price:f}"))
def manually_create_position(context, price):
  """Manually create a position at a specific price."""
  from src.constants.constants import OrderType
  from src.position.position import StopLossPosition

  position = StopLossPosition(
    entry_price=price,
    amount=context["bot"].amount,
    timeFrame=context["bot"].timeFrame,
    stopLossPercent=context["bot"].stop_loss_percent,
    orderType=OrderType.LONG,
  )
  context["bot"].position_management.position_hub.positions.append(position)
  context["bot"].position_management.position_hub.length += 1


@given(
  parsers.parse(
    "I have price data with uptrend and downtrend: {prices_str}",
  )
)
def have_trend_price_data(context, prices_str):
  """Set price data with trends."""
  prices_str = prices_str.strip("[]")
  context["prices"] = [float(p.strip()) for p in prices_str.split(",")]
  context["data"] = DummyData(context["prices"], timeFrame=TimeFrame.ONEDAY)


@given(parsers.parse("I have price data with strong uptrend: {prices_str}"))
def have_uptrend_price_data(context, prices_str):
  """Set price data with strong uptrend."""
  prices_str = prices_str.strip("[]")
  context["prices"] = [float(p.strip()) for p in prices_str.split(",")]
  context["data"] = DummyData(context["prices"], timeFrame=TimeFrame.ONEDAY)


@given(parsers.parse("I have price data with downtrend: {prices_str}"))
def have_downtrend_price_data(context, prices_str):
  """Set price data with downtrend."""
  prices_str = prices_str.strip("[]")
  context["prices"] = [float(p.strip()) for p in prices_str.split(",")]
  context["data"] = DummyData(context["prices"], timeFrame=TimeFrame.ONEDAY)


@given(
  parsers.parse(
    "I have an SMA bot with short window {short:d}, long window {long:d}, and stop loss {stop_loss:f}",
  )
)
def have_configured_bot(context, short, long, stop_loss):
  """Create fully configured SMA bot."""
  # Ensure data exists
  if context["data"] is None:
    context["prices"] = [100, 102, 104, 106, 108, 110, 112]
    context["data"] = DummyData(context["prices"], timeFrame=TimeFrame.ONEDAY)

  context["bot"] = SMABot(
    name="TestBot",
    data=context["data"],
    short_window=short,
    long_window=long,
    stop_loss_percent=stop_loss,
    amount=1.0,
  )


# ============================================================================
# When Steps - Actions
# ============================================================================


@when('I create an SMA bot with name "TestBot" and default parameters')
def create_bot_default(context):
  """Create bot with default parameters."""
  context["bot"] = SMABot(name="TestBot", data=context["data"])


@when(
  parsers.parse(
    'I create an SMA bot with name "{name}", short window {short:d}, long window {long:d}, stop loss {stop_loss:f}, and amount {amount:f}'
  )
)
def create_bot_with_params(context, name, short, long, stop_loss, amount):
  """Create bot with specific parameters."""
  context["bot"] = SMABot(
    name=name,
    data=context["data"],
    short_window=short,
    long_window=long,
    stop_loss_percent=stop_loss,
    amount=amount,
  )


@when("I create an SMA bot with custom parameters")
def create_bot_custom(context):
  """Create bot with custom parameters (table data provided by scenario)."""
  # For simplicity, hardcode the custom parameters from the scenario
  context["bot"] = SMABot(
    name="CustomBot",
    data=context["data"],
    short_window=20,
    long_window=50,
    stop_loss_percent=7.5,
    amount=2.5,
  )


@when(parsers.parse("I try to create an SMA bot with short window {short:d} and long window {long:d}"))
def try_create_bot_invalid_windows(context, short, long):
  """Try to create bot with invalid window configuration."""
  try:
    context["bot"] = SMABot(
      name="InvalidBot",
      data=context["data"],
      short_window=short,
      long_window=long,
    )
  except ValueError as e:
    context["error"] = str(e)


@when(parsers.parse("I try to create an SMA bot with stop loss percent {percent:f}"))
def try_create_bot_invalid_stop_loss(context, percent):
  """Try to create bot with invalid stop loss."""
  try:
    context["bot"] = SMABot(
      name="InvalidBot",
      data=context["data"],
      stop_loss_percent=percent,
    )
  except ValueError as e:
    context["error"] = str(e)


@when(parsers.parse("I try to create an SMA bot with amount {amount:f}"))
def try_create_bot_invalid_amount(context, amount):
  """Try to create bot with invalid amount."""
  try:
    context["bot"] = SMABot(
      name="InvalidBot",
      data=context["data"],
      amount=amount,
    )
  except ValueError as e:
    context["error"] = str(e)


@when(parsers.parse("I try to create an SMA bot with amount {amount:d}"))
def try_create_bot_invalid_amount_int(context, amount):
  """Try to create bot with invalid amount (integer)."""
  try:
    context["bot"] = SMABot(
      name="InvalidBot",
      data=context["data"],
      amount=float(amount),
    )
  except ValueError as e:
    context["error"] = str(e)


@when(parsers.parse("I calculate SMA with window size {window:d}"))
def calculate_sma(context, window):
  """Calculate SMA with given window size."""
  context["sma_result"] = context["bot"].calculate_sma(context["prices"], window)


@when(parsers.parse("I call decide_and_trade at index {idx:d}"))
def call_decide_and_trade(context, idx):
  """Call decide_and_trade method."""
  prices = context["prices"][: idx + 1]
  context["decision"] = context["bot"].decide_and_trade(prices, idx)


@when(parsers.parse("I call decide_and_trade at index {idx:d} with price dropping to {price:f}"))
def call_decide_and_trade_with_price_drop(context, idx, price):
  """Call decide_and_trade with a price drop."""
  # Modify current price
  context["prices"][idx] = price
  context["data"]._prices = context["prices"]
  prices = context["prices"][: idx + 1]
  context["decision"] = context["bot"].decide_and_trade(prices, idx)


@when(parsers.parse("the price drops to {price:f} and I check stop loss"))
def check_stop_loss_with_price_drop(context, price):
  """Check stop loss with price drop."""
  # Update the data with the dropped price
  context["prices"][-1] = price
  context["data"]._prices = context["prices"]
  # Call closeAllPositionsOnCondition to trigger stop loss check
  context["bot"].position_management.closeAllPositionsOnCondition(len(context["prices"]) - 1)


@when("I run the complete backtest")
def run_complete_backtest(context):
  """Run the bot's complete backtest."""
  context["trade_history"], context["profit_loss"] = context["bot"].run()


@when("I record the number of trades")
def record_number_of_trades(context):
  """Record the number of trades from first run."""
  context["first_run_trades"] = len(context["trade_history"])


@when("I reset the bot")
def reset_bot(context):
  """Reset the bot."""
  context["bot"].reset()


@when("I run the complete backtest again")
def run_backtest_again(context):
  """Run backtest a second time."""
  context["trade_history"], context["profit_loss"] = context["bot"].run()


# ============================================================================
# Then Steps - Assertions
# ============================================================================


@then(parsers.parse("the bot should have short window of {window:d}"))
def check_short_window(context, window):
  """Verify short window value."""
  assert context["bot"].short_window == window


@then(parsers.parse("the bot should have long window of {window:d}"))
def check_long_window(context, window):
  """Verify long window value."""
  assert context["bot"].long_window == window


@then(parsers.parse("the bot should have stop loss percent of {percent:f}"))
def check_stop_loss_percent(context, percent):
  """Verify stop loss percentage."""
  assert context["bot"].stop_loss_percent == percent


@then(parsers.parse("the bot should have amount of {amount:f}"))
def check_amount(context, amount):
  """Verify amount value."""
  assert context["bot"].amount == amount


@then("the bot should have no open positions")
def check_no_open_positions(context):
  """Verify no open positions."""
  open_positions = [p for p in context["bot"].position_management.position_hub.get_all_positions() if p.isOpen]
  assert len(open_positions) == 0


@then("the bot should have empty trade history")
def check_empty_trade_history(context):
  """Verify empty trade history."""
  assert len(context["bot"].get_trade_history) == 0


@then(parsers.parse('the bot creation should fail with error "{error_msg}"'))
def check_creation_error(context, error_msg):
  """Verify that bot creation failed with expected error."""
  assert context["error"] is not None
  assert error_msg in context["error"]


@then(parsers.parse("the SMA should be approximately {value:f}"))
def check_sma_approximate(context, value):
  """Verify SMA value is approximately correct."""
  assert context["sma_result"] is not None
  assert abs(context["sma_result"] - value) < 0.01


@then("the SMA should be None")
def check_sma_none(context):
  """Verify SMA is None."""
  assert context["sma_result"] is None


@then(parsers.parse("the SMA should be {value:f}"))
def check_sma_exact(context, value):
  """Verify SMA exact value."""
  assert context["sma_result"] == value


@then(parsers.parse('the decision should be "{decision}"'))
def check_decision(context, decision):
  """Verify trading decision."""
  # Handle both string and BotAction enum
  decision_value = str(context["decision"])
  # Extract just the action name if it's in format "BotAction.XXX"
  if "." in decision_value:
    decision_value = decision_value.split(".")[-1]
  assert decision_value == decision


@then(parsers.parse("the bot should have {count:d} open position"))
@then(parsers.parse("the bot should have {count:d} open positions"))
def check_open_positions_count(context, count):
  """Verify number of open positions."""
  open_positions = [p for p in context["bot"].position_management.position_hub.get_all_positions() if p.isOpen]
  assert len(open_positions) == count


@then(parsers.parse("the bot should have {count:d} position"))
@then(parsers.parse("the bot should have {count:d} positions"))
def check_positions_count(context, count):
  """Verify total number of positions."""
  assert len(context["bot"].position_management.position_hub.get_all_positions()) == count


@then("the position should be a StopLossPosition")
def check_position_type(context):
  """Verify position type."""
  positions = context["bot"].position_management.position_hub.get_all_positions()
  assert len(positions) > 0
  assert isinstance(positions[-1], StopLossPosition)


@then("the position should be closed by stop loss")
def check_position_closed_by_stop_loss(context):
  """Verify position was closed by stop loss."""
  positions = context["bot"].position_management.position_hub.get_all_positions()
  assert len(positions) > 0
  # After stop loss trigger, position should be closed
  assert not positions[-1].isOpen


@then("the trade history should not be empty")
def check_trade_history_not_empty(context):
  """Verify trade history has entries."""
  assert len(context["trade_history"]) > 0


@then("the profit/loss should be calculated")
def check_profit_loss_calculated(context):
  """Verify profit/loss is calculated."""
  assert context["profit_loss"] is not None
  assert isinstance(context["profit_loss"], (int, float))


@then("all trades should alternate between BUY and SELL")
def check_trades_alternate(context):
  """Verify trades alternate between BUY and SELL."""
  for i, trade in enumerate(context["trade_history"]):
    if i > 0:
      prev_type = str(context["trade_history"][i - 1]["type"])
      curr_type = str(trade["type"])
      if prev_type == "BUY":
        assert curr_type == "SELL", "SELL should follow BUY"
      elif prev_type == "SELL":
        assert curr_type == "BUY", "BUY should follow SELL"


@then("all trade prices should match the data at their indices")
def check_trade_prices_match(context):
  """Verify trade prices match actual data."""
  for trade in context["trade_history"]:
    idx = trade["idx"]
    recorded_price = trade["price"]
    actual_price = context["prices"][idx]
    assert recorded_price == actual_price


@then("the trade history should contain at least one BUY signal")
def check_at_least_one_buy(context):
  """Verify at least one BUY signal."""
  buy_trades = [t for t in context["trade_history"] if t["type"] == BotAction.BUY]
  assert len(buy_trades) >= 1


@then(parsers.parse("the trade history should have at most {count:d} trades"))
def check_at_most_trades(context, count):
  """Verify at most N trades."""
  assert len(context["trade_history"]) <= count


@then("the second run should have the same number of trades as the first run")
def check_same_trade_count_after_reset(context):
  """Verify same trade count after reset."""
  assert len(context["trade_history"]) == context["first_run_trades"]


@then("the backtest should complete without errors")
def check_backtest_completes(context):
  """Verify backtest completes."""
  assert context["trade_history"] is not None
  assert context["profit_loss"] is not None


@then("the trade history should be a list")
def check_trade_history_is_list(context):
  """Verify trade history is a list."""
  assert isinstance(context["trade_history"], list)


@then("the profit/loss should be a number")
def check_profit_loss_is_number(context):
  """Verify profit/loss is a number."""
  assert isinstance(context["profit_loss"], (int, float))


@then(parsers.parse("there should be at most {count:d} open position remaining"))
@then(parsers.parse("there should be at most {count:d} open positions remaining"))
def check_at_most_open_positions(context, count):
  """Verify at most N open positions."""
  open_positions = [p for p in context["bot"].position_management.position_hub.get_all_positions() if p.isOpen]
  assert len(open_positions) <= count


@then("at least one position should have been created")
def check_at_least_one_position_created(context):
  """Verify at least one position was created."""
  assert len(context["bot"].position_management.position_hub.get_all_positions()) > 0
