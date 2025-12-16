import sys
import urllib
from datetime import datetime

import pytest
import requests

from src.data.data import AlpacaAvailablePairs, Data, Endpoint, TimeFrame, validate_instance

sys.path.append("../")  # appends upper directory


def test_fetch_from_remote_success(mocker):
  # Arrange
  mock_response = mocker.MagicMock()
  mock_response.status_code = 200
  mock_response.json.return_value = {
    "bars": {
      "BTC/USD": [
        {"t": "2025-06-01T00:00:00Z", "o": 1, "h": 2, "l": 0.5, "c": 1.5, "v": 1000},
        {"t": "2025-06-02T00:00:00Z", "o": 1.5, "h": 2.5, "l": 1, "c": 2, "v": 1200},
      ]
    }
  }

  mocker.patch("src.data.data.requests.get", return_value=mock_response)

  data_instance = Data(
    symbol=AlpacaAvailablePairs.BTCUSD,
    timeFrame=TimeFrame.ONEDAY,
    endpoint=Endpoint.ALPACAEP0,
  )

  # Act
  status_code = data_instance.fetch_from_remote()

  # Assert
  assert status_code == 200
  assert data_instance.get_data_length() == 2
  assert data_instance.data == mock_response.json()["bars"]["BTC/USD"]


def test_fetch_from_remote_http_error(mocker):
  # Arrange
  mock_response = mocker.MagicMock()
  mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")

  mocker.patch("src.data.data.requests.get", return_value=mock_response)

  data_instance = Data(
    symbol=AlpacaAvailablePairs.BTCUSD,
    timeFrame=TimeFrame.ONEDAY,
  )

  # Act & Assert
  with pytest.raises(SystemExit):
    data_instance.fetch_from_remote()


def test_data_initialization():
  # Arrange & Act
  start_date = datetime(2025, 6, 1, 0, 0)
  end_date = datetime(2025, 6, 30, 0, 0)
  data_instance = Data(
    symbol=AlpacaAvailablePairs.TSLAUSD,
    timeFrame=TimeFrame.ONEHOUR,
    start=start_date,
    end=end_date,
    limit=500,
    fetched_from_remote=False,
  )

  # Assert
  assert data_instance.symbol == AlpacaAvailablePairs.TSLAUSD
  assert data_instance.timeFrame == TimeFrame.ONEHOUR
  assert data_instance.start == start_date
  assert data_instance.end == end_date
  assert data_instance.limit == 500
  assert data_instance.fetched_from_remote is False
  assert data_instance.get_data_length() == 0


def test_build_url():
  # Arrange
  data_instance = Data(
    symbol=AlpacaAvailablePairs.BTCUSD,
    timeFrame=TimeFrame.ONEDAY,
  )

  # Act
  url = data_instance._build_url()
  decoded_url = urllib.parse.unquote(url)

  # Assert
  assert "BTC/USD" in decoded_url
  assert "1D" in decoded_url
  assert "limit=1000" in decoded_url
  assert "data.alpaca.markets" in decoded_url


def test_build_url_custom_parameters():
  # Arrange
  start_date = datetime(2025, 1, 1, 0, 0)
  end_date = datetime(2025, 1, 31, 0, 0)
  data_instance = Data(
    symbol=AlpacaAvailablePairs.TSLAUSD,
    timeFrame=TimeFrame.FIVEMINUTES,
    start=start_date,
    end=end_date,
    limit=100,
  )

  # Act
  url = data_instance._build_url()
  decoded_url = urllib.parse.unquote(url)

  # Assert
  assert "TSLA/USD" in decoded_url
  assert "5M" in decoded_url
  assert "limit=100" in decoded_url
  assert "2025-01-01" in decoded_url
  assert "2025-01-31" in decoded_url


def test_fetch_from_remote_empty_data(mocker):
  # Arrange
  mock_response = mocker.MagicMock()
  mock_response.status_code = 200
  mock_response.json.return_value = {"bars": {"BTC/USD": []}}

  mocker.patch("src.data.data.requests.get", return_value=mock_response)

  data_instance = Data(
    symbol=AlpacaAvailablePairs.BTCUSD,
    timeFrame=TimeFrame.ONEDAY,
  )

  # Act
  status_code = data_instance.fetch_from_remote()

  # Assert
  assert status_code == 200
  assert data_instance.get_data_length() == 0
  assert data_instance.data == []


def test_fetch_from_remote_large_dataset(mocker):
  # Arrange
  large_dataset = [
    {"t": f"2025-06-{i:02d}T00:00:00Z", "o": i, "h": i + 1, "l": i - 1, "c": i + 0.5, "v": i * 100}
    for i in range(1, 31)
  ]
  mock_response = mocker.MagicMock()
  mock_response.status_code = 200
  mock_response.json.return_value = {"bars": {"BTC/USD": large_dataset}}

  mocker.patch("src.data.data.requests.get", return_value=mock_response)

  data_instance = Data(
    symbol=AlpacaAvailablePairs.BTCUSD,
    timeFrame=TimeFrame.ONEDAY,
    limit=1000,
  )

  # Act
  status_code = data_instance.fetch_from_remote()

  # Assert
  assert status_code == 200
  assert data_instance.get_data_length() == 30
  assert len(data_instance.data) == 30


def test_fetch_from_remote_not_remote_raises_error():
  # Arrange
  data_instance = Data(
    symbol=AlpacaAvailablePairs.BTCUSD,
    timeFrame=TimeFrame.ONEDAY,
    fetched_from_remote=False,
  )

  # Act & Assert
  with pytest.raises(Exception):
    data_instance.fetch_from_remote()


def test_validate_instance_valid_data():
  # Arrange
  valid_data = [
    {"t": "2025-06-01T00:00:00Z", "o": 1, "h": 2, "l": 0.5, "c": 1.5, "v": 1000},
    {"t": "2025-06-02T00:00:00Z", "o": 1.5, "h": 2.5, "l": 1, "c": 2, "v": 1200},
  ]

  # Act
  result = validate_instance(valid_data)

  # Assert
  assert result == valid_data


def test_validate_instance_invalid_data_missing_field():
  # Arrange
  invalid_data = [
    {"t": "2025-06-01T00:00:00Z", "o": 1, "h": 2, "l": 0.5, "c": 1.5},  # missing "v"
  ]

  # Act & Assert
  with pytest.raises(Exception):
    validate_instance(invalid_data)


def test_validate_instance_invalid_data_wrong_type():
  # Arrange
  invalid_data = [
    {"t": "2025-06-01T00:00:00Z", "o": "not_a_number", "h": 2, "l": 0.5, "c": 1.5, "v": 1000},
  ]

  # Act & Assert
  with pytest.raises(Exception):
    validate_instance(invalid_data)


def test_get_data_length_before_fetch():
  # Arrange
  data_instance = Data(
    symbol=AlpacaAvailablePairs.BTCUSD,
    timeFrame=TimeFrame.ONEDAY,
  )

  # Act
  length = data_instance.get_data_length()

  # Assert
  assert length == 0
