import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches

# ─── 1) CSV LADEN & VORBEREITUNG ───────────────────────────────
df = pd.read_csv(
    './btc_bars_data.csv',               # Pfad zu deiner CSV
    parse_dates=['timestamp'],
    index_col='timestamp'
)
# Zeitzone entfernen, falls vorhanden
df.index = df.index.tz_convert(None)
# Nur die benötigten Spalten
df = df[['open', 'high', 'low', 'close']]

# ─── 2) HILFSFUNKTIONEN ────────────────────────────────────────
def find_max_high(df, idxs):
    subset = df.iloc[idxs]
    t = subset['high'].idxmax()
    return {'time': t, 'price': subset.loc[t, 'high']}

def find_min_low(df, idxs):
    subset = df.iloc[idxs]
    t = subset['low'].idxmin()
    return {'time': t, 'price': subset.loc[t, 'low']}

# ─── 3) STATE-MACHINE FÜR STRONG HIGHS/LOWS ────────────────────
def detect_structure(df, debug=False):
    structure = []
    state      = 'looking_high'
    run_color  = None
    run_len    = 0
    candidate  = None

    if debug:
        plt.ion()
        fig, ax = plt.subplots(figsize=(12,6))

    for i in range(len(df)):
        row = df.iloc[i]
        color = 'green' if row['close'] > row['open'] else 'red'

        # 1) Run-Länge updaten
        if color == run_color:
            run_len += 1
        else:
            run_color, run_len = color, 1

        # 2) Zustands-Logik
        # --- looking_high → await_high ---
        if state == 'looking_high' and color == 'red' and run_len == 2 and i >= 2:
            candidate = find_max_high(df, [i-2, i-1, i])
            state = 'await_high'

        # --- await_high: Bestätigung oder Update ---
        elif state == 'await_high':
            # zwei grüne Kerzen → potenziell Strong High
            if color == 'green' and run_len == 2:
                current_high = df['high'].iat[i]
                if current_high < candidate['price']:
                    # bestätige Strong High
                    structure.append(('Strong High', candidate['time'], candidate['price']))
                    candidate, run_len = None, 0
                    state = 'looking_low'
                else:
                    # neues, höheres Weak High
                    new_wh = find_max_high(df, [i-2, i-1, i])
                    if new_wh['price'] > candidate['price']:
                        candidate = new_wh
            # zwei rote Kerzen → Weak High neu berechnen
            elif color == 'red' and run_len == 2:
                new_wh = find_max_high(df, [i-2, i-1, i])
                if new_wh['price'] > candidate['price']:
                    candidate = new_wh

        # --- looking_low → await_low ---
        elif state == 'looking_low' and color == 'green' and run_len == 2 and i >= 2:
            candidate = find_min_low(df, [i-2, i-1, i])
            state = 'await_low'

        # --- await_low: Bestätigung oder Update ---
        elif state == 'await_low':
            # zwei rote Kerzen → potenziell Strong Low
            if color == 'red' and run_len == 2:
                current_low = df['low'].iat[i]
                if current_low > candidate['price']:
                    # bestätige Strong Low
                    structure.append(('Strong Low', candidate['time'], candidate['price']))
                    candidate, run_len = None, 0
                    state = 'looking_high'
                else:
                    # neues, tieferes Weak Low
                    new_wl = find_min_low(df, [i-2, i-1, i])
                    if new_wl['price'] < candidate['price']:
                        candidate = new_wl
            # zwei grüne Kerzen → Weak Low neu berechnen
            elif color == 'green' and run_len == 2:
                new_wl = find_min_low(df, [i-2, i-1, i])
                if new_wl['price'] < candidate['price']:
                    candidate = new_wl

        # 3) Debug-Plot (optional)
        if debug:
            ax.clear()
            width = 0.8 / 24
            # Candles bis i
            for j in range(i+1):
                t = mdates.date2num(df.index[j].to_pydatetime())
                o, h, l, c = df.iloc[j][['open','high','low','close']]
                col = 'green' if c > o else 'red'
                ax.vlines(t, l, h, color='black', linewidth=1)
                rect = mpatches.Rectangle(
                    (t - width/2, min(o, c)),
                    width,
                    abs(c - o),
                    facecolor=col,
                    edgecolor='black'
                )
                ax.add_patch(rect)
            # aktueller Weak-Kandidat
            if candidate:
                t_c = mdates.date2num(candidate['time'].to_pydatetime())
                ax.scatter([t_c], [candidate['price']], marker='x', s=100, color='orange')
            # bestätigte Strongs
            for typ, t_s, p_s in structure:
                t_num = mdates.date2num(t_s.to_pydatetime())
                marker = '^' if typ=='Strong High' else 'v'
                color_m = 'green' if typ=='Strong High' else 'red'
                ax.scatter([t_num], [p_s], marker=marker, color=color_m, s=80)
            ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            ax.set_title(f'i={i}, state={state}, run_len={run_len}')
            fig.canvas.draw()
            plt.pause(0.2)

    if debug:
        plt.ioff()
        plt.show()

    return pd.DataFrame(structure, columns=['type','time','price'])

# ─── 4) Erkennung & Debug-Ausgabe ──────────────────────────────
structure_df = detect_structure(df, debug=True)
print(structure_df)
