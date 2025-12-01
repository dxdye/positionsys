import pandas as pd


class CryptoData:
  """
  Class representing cryptocurrency data.
  :param kwargs: keyword arguments containing crypto data
  :type kwargs: dict
  :return: None
  :rtype: None
  """

  def __init__(self, **kwargs):
    """
    Constructor for CryptoData class.
    Initializes the CryptoData object with provided keyword arguments.
    :param kwargs: keyword arguments containing crypto data
    :type kwargs: dict
    :return: None
    :rtype: None
    """
    self.time = None
    self.open = None
    self.high = None
    self.low = None
    self.volume = None
    self.symbol = None

    self.extract_attributes(**kwargs)

    # right now, we kinda always retrieve all the bars... perhaps we will need smth like only the latest bar? discuss

  def extract_attributes(self, **data):
    """
    Extracts attributes from the provided data dictionary.
    :param data: dictionary containing crypto data
    :type data: dict
    :return: None
    :rtype: None
    """
    self.time = data.get("timestamp")
    self.open = data.get("open")
    self.high = data.get("high")
    self.low = data.get("low")
    self.volume = data.get("volume")
    self.symbol = data.get("symbol")

  def check_if_data_fits_strategy(self):
    """
    Checks if the data fits the strategy criteria.
    :return: None
    :rtype: None
    """
    # Here we can check depending on our strategy...
    # perhaps smth like if tmp is between high and low do smth
    pass

  def validate_needed_currency(self, symbol: str):
    """
    Validates if the needed currency matches the symbol of this data.
    :param symbol: trading pair to validate against
    :type symbol: str
    :return: True if the symbol matches, False otherwise
    :rtype: bool
    """
    return self.symbol == symbol
