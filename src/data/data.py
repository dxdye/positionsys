import urllib
from datetime import datetime
from enum import Enum

import jsonschema
import requests

import src.constants.constants as consts


def validateInstance(data, schema=consts.DataValidationSchemas.ALPACA_BTC_SCHEMA.value):
  """Validate data against a given JSON schema.
  :param data: data to be validated
  :param schema: JSON schema to validate against
  :type data: any
  :type schema: dict
  :raises jsonschema.ValidationError: if the data does not conform to the schema
  :return: None
  :rtype: None
  """
  try:
    jsonschema.validate(instance=data, schema=schema)
    return data
  except jsonschema.ValidationError as e:
    print(f"Validation failed: {e.message}")
    raise


START = datetime(2025, 6, 1, 0, 0)
END = datetime(2025, 6, 30, 0, 0)


class AvailablePairs(Enum):
  """
  Enum for available trading pairs.
  Currently includes BTC/USD and TSLA/USD.
  """


class AlpacaAvailablePairs(AvailablePairs):
  """
  Enum for available trading pairs on Alpaca.
  Currently includes BTC/USD and TSLA/USD.
  """

  BTCUSD = "BTC/USD"
  TSLAUSD = "TSLA/USD"  # assuming alpaca is usede


class TimeFrame(Enum):
  """
  Enum for time frames.
  Currently includes 1 Day and 1 Month.
  """

  ONEDAY = "1D"
  ONEHOUR = "1H"
  FIVEMINUTES = "5M"
  FIFTEENMINUTES = "15M"
  ONEMINUTE = "1M"
  FOURHOURS = "4H"


class Endpoint(Enum):
  """Enum for API endpoints.
  Currently includes one endpoint for Alpaca.
  """

  ALPACAEP0 = "https://data.alpaca.markets/v1beta3/crypto/us/bars?"  # endpoint 0


class Data:
  """Class to fetch data from remote or local file.
  :param symbol: trading pair, e.g., BTC/USD
  :param timeFrame: time frame for the data, e.g., 1D, 1M
  :param start: start datetime for the data
  :param end: end datetime for the data
  :param limit: maximum number of data points to fetch
  :param endpoint: API endpoint to fetch data from
  :param fetched_from_remote: whether to fetch data from remote or local file
  :type symbol: AlpacaAvailablePairs
  :type timeFrame: TimeFrame
  :type start: datetime
  :type end: datetime
  :type limit: int
  :type endpoint: Endpoint
  :type fetched_from_remote: bool
  :raises SystemExit: if there is an HTTP error during data fetching
  :return: None
  :rtype: None
  """

  def __init__(
    self,
    symbol: AlpacaAvailablePairs,
    timeFrame: TimeFrame,
    start: datetime = START,
    end: datetime = END,
    limit: int = 1000,
    endpoint: Endpoint = Endpoint.ALPACAEP0,
    schema=consts.DataValidationSchemas.ALPACA_BTC_SCHEMA,
    fetched_from_remote: bool = True,
  ):
    """Constructor for Data class.
    Initializes the Data object with the given parameters.
    :param symbol: trading pair, e.g., BTC/USD
    :param timeFrame: time frame for the data, e.g., 1D, 1M
    :param start: start datetime for the data
    :param end: end datetime for the data
    :param limit: maximum number of data points to fetch
    :param endpoint: API endpoint to fetch data from
    :param fetched_from_remote: whether to fetch data from remote or local file
    :type symbol: AlpacaAvailablePairs
    :type timeFrame: TimeFrame
    :type start: datetime
    :type end: datetime
    :type limit: int
    :type endpoint: Endpoint
    :type fetched_from_remote: bool
    :return: None
    :rtype: None
    """
    self.symbol: AvailablePairs = symbol
    self.timeFrame = timeFrame
    self.schema = schema.value
    self.ep = endpoint
    self.limit = limit
    self.start = start
    self.end = end
    self.fetched_from_remote = fetched_from_remote

    self.length = 0
    self.loaded = False

  # self.fetchFromRemote();  could be defaultly executed..

  def _build_url(self):
    """
    Build the URL for fetching data from the API endpoint.
    :return: URL string with query parameters
    :rtype: str
    :raises: None
    """
    url = self.ep.value
    start = self.start.strftime("%Y-%m-%d")
    end = self.end.strftime("%Y-%m-%d")
    params = {
      "limit": str(self.limit),
      "timeframe": self.timeFrame.value,
      "symbols": self.symbol.value,
      "start": start,
      "end": end,
    }  # RFC-3339
    url += urllib.parse.urlencode(params)
    return url

  def fetch_from_remote(self):
    """
    Fetch data from the remote API endpoint.
    :return: HTTP status code of the response
    :rtype: int
    :raises SystemExit: if there is an HTTP error during data fetching
    """
    if not self.fetched_from_remote:
      raise "resource should be fetched from file"
    url = self._build_url()
    try:
      r = requests.get(url)  # will be the data parsed into json
      r.raise_for_status()
      self.data = r.json()["bars"][self.symbol.value]
      self.data = validateInstance(self.data, self.schema)
      self.length = len(self.data)

      if r.status_code == 200:
        self.loaded = True

      return r.status_code
    except requests.exceptions.HTTPError as err:
      raise SystemExit(err)

  def getDataAtIndex(self, index: int) -> dict:
    """
    Get data point at the specified index.
    :param index: index of the data point to retrieve
    :type index: int
    :return: data point at the specified index
    :rtype: dict
    :raises IndexError: if the index is out of range
    """
    if not self.loaded:
      raise "data not loaded yet"
    if index < 0 or index >= self.length:
      raise IndexError("Index out of range")
    return self.data[index]

  def getDataLength(self):
    """
    Get the length of the fetched data.
    :return: length of the data
    :rtype: int
    """
    return self.length

  def getClosingPrices(self) -> list[float]:
    """
    Get all closing prices from the loaded data.
    :return: list of closing prices
    :rtype: list[float]
    :raises: RuntimeError if data not loaded yet
    """
    if not self.loaded:
      raise RuntimeError("data not loaded yet")
    return [self.data[i]["c"] for i in range(self.length)]

  def getFromFile(self):
    """
    Fetch data from a local file.
    :return: None
    :rtype: None
    :raises: NotImplementedError
    """
    pass

  pass
