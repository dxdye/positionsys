from enum import Enum;
import requests; 
import urllib; 

class ValueTypes(Enum):
    STOCK = "STOCK"
    CRYPTO = "CRYPTO"
    OPTION = "OPTION"

class AlpacaAvailablePairs(Enum): 
    BTCUSD = "BTC/USD"
    TSLAUSD = "TSLA/USD" #assuming alpaca is usede

class TimeFrame(Enum): 
    ONEDAY = "1D"
    ONEMONTH = "1M"
    #..etc
    

class Endpoint(Enum):
    ALPACAEP0 = "https://data.alpaca.markets/v1beta3/crypto/us/bars?" #endpoint 0

class Data:
    def __init__(self, symbol: AlpacaAvailablePairs, typeOfData: ValueTypes, timeFrame: TimeFrame, limit: int = 1000, endpoint: Endpoint = Endpoint.ALPACAEP0, fetchedFromRemote: bool = True):
        self.symbol = symbol; 
        self.typeOfData = typeOfData; 
        self.timeFrame = timeFrame; 
        self.ep = endpoint; 
        self.limit = limit;  
        self.fetchedFromRemote = fetchedFromRemote; 
        #self.fetchFromRemote();  could be defaultly executed..
    def buildUrl(self): 
        url = self.ep.value; 
        params = {'limit': str(self.limit), 'timeframe': self.timeFrame.value, 'symbols': self.symbol.value,}
        url += urllib.parse.urlencode(params);
        print(url) 
        return url; 

    def fetchFromRemote(self):
        if not self.fetchedFromRemote: raise "resource should be fetched from file.. pls think about this."; 
        url = self.buildUrl(); 
        try: 
            r = requests.get(url); # will be the data parsed into json
            r.raise_for_status(); 
            data = r.json();
            return r.status_code; 
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)
        


    def getFromFile(self):
        pass
    #add meta data, time frame, begin and end
    pass
