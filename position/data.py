from enum import Enum;

class DataType(Enum):
    STOCK,
    CRYPTO,
    OPTION

class AlpacaAvailablePairs(Enum): 
    BTCUSD = "BTC/USD",
    TSLAUSD = "TSLA/USD" #assuming alpaca is usede


class Data:


    def __init__(self, symbol: AlpacaAvailablePairs, typeOfData: DataType):
        self.symbol = symbol; 
        self.typeOfData = typeOfData; 
    def getFromRemote(self):
        pass
    def getFromFile(self):
        pass
    #add meta data, time frame, begin and end
    pass
