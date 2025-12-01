import pandas as pd


class CryptoData:
  def __init__(self, **kwargs):
    self.time = None
    self.open = None
    self.high = None
    self.low = None
    self.volume = None
    self.symbol = None

    self.extract_attributes(**kwargs)

    # right now, we kinda always retrieve all the bars... perhaps we will need smth like only the latest bar? discuss

  def extract_attributes(self, **data):
    self.time = data.get("timestamp")
    self.open = data.get("open")
    self.high = data.get("high")
    self.low = data.get("low")
    self.volume = data.get("volume")
    self.symbol = data.get("symbol")

  def check_if_data_fits_strategy(self):
    # Here we can check depending on our strategy...
    # perhaps smth like if tmp is between high and low do smth
    pass

  def validate_needed_currency(self, symbol: str):
    return self.symbol == symbol
