import sys
sys.path.append('../')
import data.data as mod; 
#from mod import *; 


def testDataWorkflow(): 
    data0 = mod.Data(mod.AlpacaAvailablePairs.BTCUSD, mod.TimeFrame.ONEDAY, mod.DataType.STOCK)
    data0.fetchFromRemote(); 






