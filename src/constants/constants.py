from enum import Enum

LIMIT = 10000
SMALLEST_INVEST = 0.01


class OrderType(Enum):
  LONG = "long"
  SHORT = "short"


class BotAction(Enum):
  BUY = "BUY"
  SELL = "SELL"
  HOLD = "HOLD"
  SKIP = "SKIP"


class DataValidationSchemas(Enum):
  ALPACA_BTC_SCHEMA = {
    "type": "array",
    "items": {
      "type": "object",
      "properties": {
        "t": {"type": "string", "format": "date-time"},
        "o": {"type": "number"},
        "h": {"type": "number"},
        "l": {"type": "number"},
        "c": {"type": "number"},
        "v": {"type": "number"},
      },
      "required": ["t", "o", "h", "l", "c", "v"],
    },
  }


class PositionType(Enum):
  """Enum for different types of positions."""

  BASIC = "basic"
  STOP_LOSS = "stop_loss"
  TAKE_PROFIT = "take_profit"  # not implemented yet
  # Add more position types as needed
