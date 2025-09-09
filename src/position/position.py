import sys

sys.path.append("../")
import data.data as data
from datetime import datetime

LIMIT = 10000
SMALLEST_INVEST = 0.01


class Position:
    def __init__(self, amount, positionId):
        self.createdAt = datetime.now()
        self.isOpen = True
        if amount < 0:
            raise "amount has to be bigger than 0"
        self.amount = amount
        self.id = positionId  # maybe important later
        self.closedAt = None

    def close(
        self,
    ):
        if self.isOpen == True:
            self.isOpen = False
            self.closedAt = datetime.now()
        else:
            raise "position is already closed"

    def createDummyPosition(self, begin, close, amount):
        self.createdAt = begin
        self.closedAt = close
        self.amount = amount


class PositionHub:
    def __init__(
        self,
    ):
        self.positions: List[Position] = []  # stack of positions LIFO
        length = 0

    # open new position

    def checkConsitency():
        if length == 0:
            return
        if length != len(self.position):
            raise "length is representative for the positionId and should be updated accuratly"
        # is of type [position]
        # only last position can be open or closed
        # every other is closed
        # the one opened is not followed by any other
        for i in self.positions:
            if type(i) is not Position:
                raise "element is of wrong type"
        if length > 1:
            for i in range(self.position - 1):
                if self.positions[i].isOpen is True:
                    raise "every position prior last should be closed"
        return

    def closeLatestPosition(self):
        self.checkConsitency()
        if len(self.positions) is 0:
            raise "no positions existant"

        latestPosition: Position = self.positions[-1]
        if not (latestPosition.isOpen):
            return  # latest position already closed - stop here.
        if self.latestPosition.closedAt is None:  ##dreifach hält besser
            continue
        self.latestPosition.close()

    def openNewPosition(self, amount):
        # close old position automatically
        if amount < SMALLEST_INVEST:
            raise "stop here. amount should be bigger than smallest possible invest"
        if length >= 1:  # when positions existant
            closeLatestPosition()
        self.positions.append(Position((amount, self.length + 1)))
        self.checkConsitency()
        self.length += 1  # id defined via length

    def getAllPositions(self):
        return self.positions


class PositionSimulation:  # this only evaluates the
    def __init__(
        self,
        data: data.Data,
        balance=200,
        limit=LIMIT,
    ):
        self.positionHub = PositionHub()
        self.balance = balance
        self.limit = limit  # limit of investing assets
        self.variation = None  # this will include the proft and loss for every tick
        # -> maybe better to put this into the position?
        # nope - the idea is to calculate that 'live' in the reevaluation
        # this can be actually visualized

        self.data = data

    # will be iterated on later to calculate loss profit

    def reevaluate(self):
        # Positionen operieren auf den Daten - Evaluation aller Positionen
        quantize = self.data.timeFrame
        iterations = self.data.getDataLength()
        positions: [Position] = self.positionHub.getAllPositions()
        for pos in positions:
            # nun hier werden wir die Daten brauchen -> das Problem ist allerdings das
            # timestamps aufgerundet werden auf den jeweiligen nächsten tick
            # zudem können bei klines nur die open und close preise verwertet werden
            # eigentlich wären hier minütliche Datenpflicht
            # um jedoch einen ausreichenden Datenrahmen zu bekommen hätte man
            # die JSON verschiedener Responses zu konkatenieren.
            pass

    def bot(self):
        # bot operiert auf den Daten und schließt/ öffnet Position
        pass
