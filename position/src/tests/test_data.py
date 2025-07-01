import sys
sys.path.append('../')
import data.data as mod; 


def testDataWorkflow(): 
    #this is a stub which is not really a test.
    data0 = mod.Data(symbol=mod.AlpacaAvailablePairs.BTCUSD, 
                     typeOfData=mod.ValueTypes.CRYPTO, 
                     timeFrame=mod.TimeFrame.ONEDAY)
    status = data0.fetchFromRemote(); 
    assert 200 == status; 







