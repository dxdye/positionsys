from datetime import datetime, timedelta

from src.data import data


def mapIndexToTime(timeFrame: data.TimeFrame, index: int) -> datetime:
  """
  Maps the index of the data to the corresponding time based on the given timeframe.
  :param timeFrame: The timeframe of the data.
  :param index: The index in the data.
  :return: The corresponding datetime for the given index and timeframe.
  :rtype: datetime
  """
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
    raise TypeError("unsupported timeframe")
