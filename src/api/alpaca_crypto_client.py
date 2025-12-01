import datetime

from alpaca.data import CryptoBarsRequest
from alpaca.data.historical import CryptoHistoricalDataClient
from alpaca.data.timeframe import TimeFrame

from src.api.crypto_data import CryptoData


class AlpacaCryptoClient:
  # here we dont need api key and secret, the data is also limited from what ive seen tough
  """
  Client to interact with Alpaca Crypto Historical Data API.
  Provides methods to fetch historical crypto data.
  :raises Exception: if there is an error during API request
  :return: None
  :rtype: None
  """

  def __init__(self):
    self.client = CryptoHistoricalDataClient()

  def get_crypto_bars(self, symbol: str, start_date: datetime, end_date: datetime):
    """
    Fetches historical crypto bars data for a given symbol and date range.
    :param symbol: trading pair, e.g., BTC/USD
    :param start_date: start datetime for the data
    :param end_date: end datetime for the data
    :type symbol: str
    :type start_date: datetime
    :type end_date: datetime
    :raises Exception: if there is an error during API request
    :return: list of CryptoData objects containing the historical data
    :rtype: list[CryptoData]
    """
    params = CryptoBarsRequest(symbol_or_symbols=symbol, timeframe=TimeFrame.Day, start=start_date, end=end_date)
    try:
      response = self.client.get_crypto_bars(params)
      print("succesfully retrieved Crypto data!")
      bars = response.df.reset_index().to_dict(orient="records")
      return [CryptoData(**bar) for bar in bars]
    except Exception as e:
      print(e)

  # not sure if we need more methods/api endpoints?? gotta discuss with colleagues


if __name__ == "__main__":
  client = AlpacaCryptoClient()
  end_date = datetime.datetime.today()
  start_date = end_date - datetime.timedelta(days=7)
  bars = client.get_crypto_bars("BTC/USD", start_date, end_date)
  for bar in bars:
    print(bar)
