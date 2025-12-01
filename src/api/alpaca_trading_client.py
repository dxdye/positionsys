import requests


class AlpacaTradingClient:
  BASE_URL = "https://paper-api.alpaca.markets"
  # we always use paper right now, this class also needs api key and secret

  """
  Client to interact with Alpaca Trading API.
  Provides methods to fetch and manage trading positions.
  :param api_key: Alpaca API key
  :param api_secret: Alpaca API secret
  :type api_key: str
  :type api_secret: str
  :raises Exception: if there is an error during API request
  :return: None
  :rtype: None
  """

  def __init__(self, api_key, api_secret):
    self.api_key = api_key
    self.api_secret = api_secret
    self.base_url = AlpacaTradingClient.BASE_URL
    self.headers = {
      "APCA-API-KEY-ID": self.api_key,
      "APCA-API-SECRET-KEY": self.api_secret,
      "accept": "application/json",
    }

  """
  Fetches all open positions from the Alpaca Trading API.
  :raises Exception: if there is an error during API request
  :return: list of open positions
  :rtype: list
  """

  def get_open_positions(self):
    # https://docs.alpaca.markets/reference/getallopenpositions
    url = self.base_url + "/v2/positions"
    try:
      response = requests.get(url, headers=self.headers)
      response.raise_for_status()
      return response.json()
    except Exception as e:
      print(e)

  """
  Fetches a specific position by symbol or asset ID from the Alpaca Trading API.
  :param symbol_or_asset_id: symbol or asset ID of the position to fetch
  :type symbol_or_asset_id: str
  :raises Exception: if there is an error during API request
  :return: position data
  :rtype: dict
  """

  def get_specific_position(self, symbol_or_asset_id: str):
    url = self.base_url + "/v2/positions/" + f"{symbol_or_asset_id}"
    try:
      response = requests.get(url, headers=self.headers)
      response.raise_for_status()
      return response.json()
    except Exception as e:
      print(e)

  """
  Fetches a specific position from all positions by symbol.
  :param symbol: symbol of the position to fetch
  :type symbol: str
  :return: position data if found, else None
  :rtype: dict or None
  """

  def retrive_specific_pos_from_all_positions(self, symbol=str):
    positions = self.get_positions()
    for p in positions:
      if p["symbol"] == symbol:
        return p
    print("no such symbol was found in the positions!")
    return None

  """
  Closes a specific position by symbol or asset ID using the Alpaca Trading API.
  :param symbol_or_asset_id: symbol or asset ID of the position to close
  :type symbol_or_asset_id: str
  :raises Exception: if there is an error during API request
  :return: None
  :rtype: None
  """

  def close_position(self, symbol_or_asset_id: str):
    url = self.base_url + "/v2/positions/" + f"{symbol_or_asset_id}"
    try:
      response = requests.delete(url, headers=self.headers)
      response.raise_for_status()
      print(response.text)
    except Exception as e:
      print(e)

  # we probably need orders api points here... i dont know
  """
  Places an order using the Alpaca Trading API.
  :param type: type of the order (e.g., market, limit)
  :param symbol: trading symbol for the order
  :param time_in_force: time in force for the order (e.g., day,
    gtc)
  :param qty: quantity for the order (optional)
  :param notional: notional value for the order (optional)
  :type type: str
  :type symbol: str
  :type time_in_force: str
  :type qty: str or None
  :type notional: str or None
  :raises Exception: if there is an error during API request
  :return: None
  :rtype: None
  """

  def place_order(self, type: str, symbol: str, time_in_force: str, qty: str = None, notional: str = None):
    url = self.base_url + "/v2/orders"
    payload = {"type": type, "symbol": symbol, "time_in_force": time_in_force, "qty": qty, "notional": notional}
    try:
      response = requests.post(url, json=payload, headers=self.headers)
      response.raise_for_status()
      print(response.text)
    except Exception as e:
      print(e)
