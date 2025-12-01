import requests


class AlpacaTradingClient:
  BASE_URL = "https://paper-api.alpaca.markets"
  # we always use paper right now, this class also needs api key and secret

  def __init__(self, api_key, api_secret):
    self.api_key = api_key
    self.api_secret = api_secret
    self.base_url = AlpacaTradingClient.BASE_URL
    self.headers = {
      "APCA-API-KEY-ID": self.api_key,
      "APCA-API-SECRET-KEY": self.api_secret,
      "accept": "application/json",
    }

  def get_open_positions(self):
    # https://docs.alpaca.markets/reference/getallopenpositions
    url = self.base_url + "/v2/positions"
    try:
      response = requests.get(url, headers=self.headers)
      response.raise_for_status()
      return response.json()
    except Exception as e:
      print(e)

  def get_specific_position(self, symbol_or_asset_id: str):
    url = self.base_url + "/v2/positions/" + f"{symbol_or_asset_id}"
    try:
      response = requests.get(url, headers=self.headers)
      response.raise_for_status()
      return response.json()
    except Exception as e:
      print(e)

  def retrive_specific_pos_from_all_positions(self, symbol=str):
    positions = self.get_positions()
    for p in positions:
      if p["symbol"] == symbol:
        return p
    print("no such symbol was found in the positions!")
    return None

  def close_position(self, symbol_or_asset_id: str):
    url = self.base_url + "/v2/positions/" + f"{symbol_or_asset_id}"
    try:
      response = requests.delete(url, headers=self.headers)
      response.raise_for_status()
      print(response.text)
    except Exception as e:
      print(e)

  # we probably need orders api points here... i dont know

  def place_order(self, type: str, symbol: str, time_in_force: str, qty: str = None, notional: str = None):
    url = self.base_url + "/v2/orders"
    payload = {"type": type, "symbol": symbol, "time_in_force": time_in_force, "qty": qty, "notional": notional}
    try:
      response = requests.post(url, json=payload, headers=self.headers)
      response.raise_for_status()
      print(response.text)
    except Exception as e:
      print(e)
