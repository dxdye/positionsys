from enum import Enum;
import requests; 
from datetime import datetime; 
import urllib; 

START = datetime(2025, 6, 1, 0, 0); 
END = datetime(2025, 6, 30, 0, 0); 

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
    def __init__(self, symbol: AlpacaAvailablePairs, timeFrame: TimeFrame, start:datetime = START, end: datetime = END,  limit: int = 1000, endpoint: Endpoint = Endpoint.ALPACAEP0, fetchedFromRemote: bool = True):
        self.symbol = symbol; 
        self.timeFrame = timeFrame; 
        self.ep = endpoint; 
        self.limit = limit;  
        self.fetchedFromRemote = fetchedFromRemote; 
        self.start = start; 
        self.end = end; 
        self.length = 0; 
        #self.fetchFromRemote();  could be defaultly executed..

    def buildUrl(self): 
        url = self.ep.value; 
        start = self.start.strftime('%Y-%m-%d')
        end = self.end.strftime('%Y-%m-%d')
        params = {'limit': str(self.limit), 'timeframe': self.timeFrame.value, 'symbols': self.symbol.value,
                    'start': start, 'end': end } # RFC-3339
        url += urllib.parse.urlencode(params);
        return url; 

    def fetchFromRemote(self):
        if not self.fetchedFromRemote: raise "resource should be fetched from file.. pls think about this."; 
        url = self.buildUrl(); 
        try: 
            r = requests.get(url); # will be the data parsed into json
            r.raise_for_status(); 
            self.data = r.json()['bars']['BTC/USD']; #defaultly take those values
            self.length = len(self.data); 
            print(self.data); 

            return r.status_code; 

        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)

    def getDataLength(self): 
        return self.length; 

    def getFromFile(self):
        pass
    #add meta data, time frame, begin and end
    pass
