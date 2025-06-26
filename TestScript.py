
import pandas as pd
from alpaca.data.historical import CryptoHistoricalDataClient
from alpaca.data.requests import CryptoBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
# No keys required for crypto data
client = CryptoHistoricalDataClient()


# Creating request object
tf = TimeFrame(amount=1, unit=TimeFrameUnit.Hour)

request_params = CryptoBarsRequest(
  symbol_or_symbols=["BTC/USD"],
  timeframe=tf,
  start=datetime(2025, 5, 1),
  end=datetime(2025, 5, 27)
)


# Retrieve daily bars for Bitcoin in a DataFrame and printing it
btc_bars = client.get_crypto_bars(request_params)
btc_df = btc_bars.df



#data.set_index('timestamp', inplace=True)

# Farbe der Candle
btc_df['color'] = btc_df.apply(lambda row: 'green' if row['close'] > row['open'] else 'red', axis=1)



# Ergebnisliste für bestätigte Strong Highs / Lows
structure = []

# Weak-Kandidaten
candidate_WH = None
candidate_WL = None

# Letzte bestätigte Strong-Punkte und ihr Typ
last_SH = None
last_SL = None
last_type = None  # 'Strong High' oder 'Strong Low'

# Zähler für gleichfarbige Kerzen
up_count = 0
down_count = 0

# Temporäre Extrema innerhalb der Farbserie
max_high = None
max_high_time = None
min_low = None
min_low_time = None

for i in range(1, len(btc_df)):
    prev = btc_df.iloc[i-1]
    curr = btc_df.iloc[i]

    # ——— Aufwärtsserie (grün) —————————————————————————————
    if curr['color'] == 'green':
        if prev['color'] == 'green':
            up_count += 1
        else:
            up_count = 1
            # neue Serie → Hoch-Extremum zurücksetzen
            max_high = curr['high']
            max_high_time = curr.name
        down_count = 0

        # Hoch aktualisieren (erstes Mal oder neues höheres)
        if max_high is None or curr['high'] > max_high:
            max_high = curr['high']
            max_high_time = curr.name

    # ——— Abwärtsserie (rot) ——————————————————————————————
    elif curr['color'] == 'red':
        if prev['color'] == 'red':
            down_count += 1
        else:
            down_count = 1
            # neue Serie → Tief-Extremum zurücksetzen
            min_low = curr['low']
            min_low_time = curr.name
        up_count = 0

        # Tief aktualisieren (erstes Mal oder neues tieferes)
        if min_low is None or curr['low'] < min_low:
            min_low = curr['low']
            min_low_time = curr.name

    else:
        # falls andere Farbe
        up_count = down_count = 0
        max_high = max_high_time = None
        min_low  = min_low_time  = None

    # ——— 1) Weak High erkennen ————————————————————————
    if down_count == 2 and candidate_WH is None and max_high_time is not None:
        candidate_WH = {'time': max_high_time, 'price': max_high}

    # ——— 2) Weak Low erkennen ————————————————————————
    if up_count == 2 and candidate_WL is None and min_low_time is not None:
        candidate_WL = {'time': min_low_time, 'price': min_low}

    # ——— 3) WH → SH (nach 2 grünen Kerzen) —————————————
    if candidate_WH is not None and up_count == 2:
        # a) zunächst das neue Weak Low zwischenspeichern (für späteren SL)
        if min_low_time is not None:
            candidate_WL = {'time': min_low_time, 'price': min_low}

        # b) nur dann zum Strong High machen, wenn
        #    • der letzte Typ nicht schon SH war (Alternanz) UND
        #    • der Preis höher ist als das letzte SH (wenn vorhanden)
        if last_type != 'Strong High' and (last_SH is None or candidate_WH['price'] > last_SH['price']):
            structure.append({
                'type':  'Strong High',
                'time':  candidate_WH['time'],
                'price': candidate_WH['price']
            })
            last_SH = candidate_WH
            last_type = 'Strong High'

        # c) aufräumen
        candidate_WH = None
        max_high = None
        max_high_time = None

    # ——— 4) WL → SL (nach 2 roten Kerzen) ——————————————
    if candidate_WL is not None and down_count == 2:
        # a) neues Weak High zwischenspeichern (für späteren SH)
        if max_high_time is not None:
            candidate_WH = {'time': max_high_time, 'price': max_high}

        # b) nur dann zum Strong Low machen, wenn
        #    • der letzte Typ nicht schon SL war (Alternanz) UND
        #    • der Preis tiefer ist als das letzte SL (wenn vorhanden)
        if last_type != 'Strong Low' and (last_SL is None or candidate_WL['price'] < last_SL['price']):
            structure.append({
                'type':  'Strong Low',
                'time':  candidate_WL['time'],
                'price': candidate_WL['price']
            })
            last_SL = candidate_WL
            last_type = 'Strong Low'

        # c) aufräumen
        candidate_WL = None
        min_low = None
        min_low_time = None

# Ausgabe als DataFrame
structure_df = pd.DataFrame(structure)
print(structure_df)
