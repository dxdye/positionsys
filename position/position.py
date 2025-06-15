
import datetime

class Position: 
    def __init__(self, amount, positionId): 
        self.createdAt = datetime.date(); 
        self.isOpen = True; 
        if amount < 0: 
            raise "amount has to be bigger than 0";
        self.amount = amount; 
        self.id = positionId; 
        self.closedAt = None;
    def close(self,):
        if self.isOpen == True:
            self.isOpen = false; 
            self.closedAt = datetime.date();
        else: raise "position is already closed"; 

class PositionHub: 
    def __init__(self,): 
        self.positions: List[Position] = []; #stack of positions LIFO
        length=0; 
        #open new position 

    def checkConsitency(): 
        if length == 0: return; 
        if length != len(self.position): raise "length is representative for the positionId and should be updated accuratly"; 
        #is of type [position]
        #only last position can be open or closed 
        #every other is closed
        #the one opened is not followed by any other
        for i in self.positions: 
            if type(i) is not Position: raise "element is of wrong type"; 
        if length > 1: 
            for i in range(self.position-1): 
                if self.positions[i].isOpen is True: raise "every position prior last should be closed"; 
        return;         

    def closeLatestPosition(self): 
        self.checkConsitency(); 
        if len(self.positions) is 0: raise "no positions existant"; 

        latestPosition: Position = self.positions[-1];
        if not (latestPosition.isOpen): return; #latest position already closed - stop here.
        if self.latestPosition.closedAt is None: ##dreifach hält besser
            continue
        self.latestPosition.close()

    def openNewPosition(self, amount): 
        #close old position automatically
        if length >= 1: #when positions existant
            closeLatestPosition(); 

        self.positions.append(Position((amount, self.length + 1)))
        self.checkConsitency();
        self.length+=1 #id defined via length
            

LIMIT = 10000
class PositionSimulation: 
    def __init__(self, balance, limit=LIMIT):
        self.positionHub = PositionHub(); 
        self.balance = balance; 
        self.limit = limit #limit of investing assets
        self.variation = None; #this will include the win and drawbacks for every tick
    def reevaluate(): 
        pass

    
