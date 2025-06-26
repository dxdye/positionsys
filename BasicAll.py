import pandas as pd
from datetime import datetime
from alpaca.data.historical import CryptoHistoricalDataClient
from alpaca.data.requests import CryptoBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from mplfinance.original_flavor import candlestick_ohlc

# ─── 1) DATEN LADEN & INDEX BEREINIGEN ─────────────────────────
client = CryptoHistoricalDataClient()
tf     = TimeFrame(amount=1, unit=TimeFrameUnit.Hour)
req    = CryptoBarsRequest(
    symbol_or_symbols=["BTC/USD"],
    timeframe=tf,
    start=datetime(2025, 5, 1),
    end  =datetime(2025, 5, 27)
)
bars   = client.get_crypto_bars(req)
df     = bars.df.reset_index(level=0, drop=True)
df.index = pd.to_datetime(df.index)    # reiner DatetimeIndex

# ─── 2) STRONG HIGH/LOW-ERKENNUNG via STATE-MACHINE ────────────
structure = []
state     = 'looking_high'   # wechselt: looking_high → await_high → looking_low → await_low → looking_high …
run_color = None
run_len   = 0
cand_time = None
cand_price= None

for i in range(len(df)):
    idx  = df.index[i]
    row  = df.iloc[i]
    # Farbe der Kerze
    color = 'green' if row['close'] > row['open'] else 'red'
    # Consecutive-Run updaten
    if color == run_color:
        run_len += 1
    else:
        run_color = color
        run_len   = 1

    # Vorherige Kerze
    if i > 0:
        prev_idx = df.index[i-1]
        prev_row = df.iloc[i-1]
    else:
        prev_idx = None
        prev_row = None

    # 1) looking_high: 2 rote Kerzen → Weak High
    if state == 'looking_high' and color == 'red' and run_len == 2:
        # wähle das höhere Hoch der beiden Kerzen
        if prev_row['high'] >= row['high']:
            cand_time, cand_price = prev_idx, prev_row['high']
        else:
            cand_time, cand_price = idx,       row['high']
        state = 'await_high'
        continue

    # 2) await_high: 2 grüne Kerzen → Strong High
    if state == 'await_high' and color == 'green' and run_len == 2:
        structure.append(('Strong High', cand_time, cand_price))
        state = 'looking_low'
        continue

    # 3) looking_low: 2 grüne Kerzen → Weak Low
    if state == 'looking_low' and color == 'green' and run_len == 2:
        # wähle das tiefere Tief der beiden Kerzen
        if prev_row['low'] <= row['low']:
            cand_time, cand_price = prev_idx, prev_row['low']
        else:
            cand_time, cand_price = idx,       row['low']
        state = 'await_low'
        continue

    # 4) await_low: 2 rote Kerzen → Strong Low
    if state == 'await_low' and color == 'red' and run_len == 2:
        structure.append(('Strong Low', cand_time, cand_price))
        state = 'looking_high'
        continue

# In DataFrame umwandeln
structure_df = pd.DataFrame(structure, columns=['type','time','price'])
structure_df['time'] = pd.to_datetime(structure_df['time'])
structure_df = structure_df.sort_values('time')

# ─── 3) PLOT VORBEREITUNG ──────────────────────────────────────
# 3.1 OHLC für candlestick_ohlc
ohlc = df.copy()
ohlc['t_num'] = mdates.date2num(ohlc.index.to_pydatetime())
ohlc_vals = ohlc[['t_num','open','high','low','close']].values

# 3.2 Punkte für SH / SL
sh = structure_df[structure_df['type']=='Strong High']
sl = structure_df[structure_df['type']=='Strong Low']
times_sh  = mdates.date2num(sh['time'].dt.to_pydatetime())
prices_sh = sh['price'].values
times_sl  = mdates.date2num(sl['time'].dt.to_pydatetime())
prices_sl = sl['price'].values

# 3.3 Verbindungslinie
times_all  = mdates.date2num(structure_df['time'].dt.to_pydatetime())
prices_all = structure_df['price'].values

# ─── 4) PLOT RENDERN ───────────────────────────────────────────
fig, ax = plt.subplots(figsize=(14,6))

# a) Candlestick-Chart
candlestick_ohlc(
    ax,
    ohlc_vals,
    width=0.03,
    colorup='green',
    colordown='red'
)

# b) Pfeile für Strong High / Low
ax.scatter(times_sh, prices_sh, marker='^', s=100, color='green', label='Strong High')
ax.scatter(times_sl, prices_sl, marker='v', s=100, color='red',   label='Strong Low')

# c) Linie durch alle Punkte
ax.plot(times_all, prices_all, '-', lw=1, color='blue', label='Struktur-Verlauf')

# d) xticks jede Stunde (oder interval=3 für 3-Stunden-Ticks)
ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d\n%H:%M'))
plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

# e) Beschriftungen & Legende
ax.set_xlabel('Zeit')
ax.set_ylabel('Preis (USD)')
plt.title('BTC/USD – Stundenkerzen mit Strong Highs/Lows')
ax.legend(loc='best')
plt.tight_layout()
plt.show()
