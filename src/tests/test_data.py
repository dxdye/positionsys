import sys
from pytest_bdd import when
import data.data as mod

sys.path.append("../")  # appends upper directory


def testDataWorkflow():
  """a stub which is not really a test."""
  data0 = mod.Data(
    symbol=mod.AlpacaAvailablePairs.BTCUSD,
    timeFrame=mod.TimeFrame.ONEDAY,
  )
  url = data0.buildUrl()
  status = data0.fetchFromRemote()
  assert 200 == status
