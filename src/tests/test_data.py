import sys
sys.path.append('../') #appends upper directory
import data.data as mod; 


def testDataWorkflow(): 
    #this is a stub which is not really a test.
    data0 = mod.Data(symbol=mod.AlpacaAvailablePairs.BTCUSD, 
                     timeFrame=mod.TimeFrame.ONEDAY)
    url = data0.buildUrl(); 
    assert data0.buildUrl() == "https://data.alpaca.markets/v1beta3/crypto/us/bars?limit=1000&timeframe=1D&symbols=BTC%2FUSD"; 
    status = data0.fetchFromRemote(); 
    assert 200 == status; 







