
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
        self.positions = [Position]; 
        #open new position 

    def checkConsitency(): 
        #is of class position
        #only one position is open
        #the one opened is not followed by any other
        pass

    
