import pandas as pd 
import ta
import matplotlib.pyplot as plt 
import mplfinance as mpf

# Data read
data = pd.read_csv("TSLA.csv", parse_dates=['Date'])
data = data.sort_values('Date')

# Making sure data clean
data['Close'] = pd.to_numeric(data['Close'], errors='coerce')
data['Volume'] = pd.to_numeric(data['Volume'], errors='coerce')

# Indicators calc
data['ema_10'] = ta.trend.ema_indicator(data['Close'], window=10)
data['ema_20'] = ta.trend.ema_indicator(data['Close'], window=20)
data['vwma_20'] = (data['Close'] * data['Volume']).rolling(20).sum() / data['Volume'].rolling(20).sum()
data['rsi_14'] = ta.momentum.rsi(data['Close'], window=14)

start_cash = 10000
have_pos = False
buy_price = 0
my_trades = []

# backtest loop
for idx in range(1, len(data)):
   now = data.iloc[idx]
   before = data.iloc[idx-1]
   
   if have_pos == False:
     # entry rules
     cross_up = before['ema_10'] < before['vwma_20'] and now['ema_10'] > now['vwma_20']
     if cross_up and now['rsi_14']<30:
        buy_price = now['Close']
        buy_time = now['Date']
        have_pos = True
        start_cash -= 2  # brokage fees
   else:
      current_price = now['Close']
      move_pct = (current_price - buy_price) / buy_price
      
      tp = move_pct >= 0.1
      sl = move_pct <= -0.05
      cross_down = before['ema_10'] > before['ema_20'] and now['ema_10'] < now['ema_20'] and now['rsi_14'] > 70
      
      if tp or sl or cross_down:
           sell_price = current_price
           sell_time = now['Date']
           pl = (sell_price - buy_price) - 2  # exit fee
           start_cash += (sell_price - 2)
           
           my_trades.append({
               'buy_time': buy_time,
               'sell_time': sell_time,
               'buy_price': buy_price,
               'sell_price': sell_price,
               'profit': pl if pl > 0 else 0,
               'loss': abs(pl) if pl < 0 else 0,
               'sl_hit': sl,
               'tp_hit': tp
           })
           have_pos = False

# trades df
tradesheet = pd.DataFrame(my_trades)

# result
if tradesheet.empty:
   print("oops no trades happened")
else:
    tot_profit = tradesheet['profit'].sum()
    tot_loss = tradesheet['loss'].sum()
    trade_count = len(tradesheet)
    wins = len(tradesheet[tradesheet['profit'] > 0])
    loses = len(tradesheet[tradesheet['loss'] > 0])
    ratio = (tot_profit / tot_loss) if tot_loss > 0 else 'infinite'
    
    print(f"End Capital: {round(start_cash,2)}")
    print(f"Trades Done: {trade_count}")
    print(f"Winning Trades: {wins}")
    print(f"Losing Trades: {loses}")
    print(f"Profit to Loss Ratio: {ratio}")
    
    print("\n--- All Trades ---")
    print(tradesheet)

    # plotting
    entries = tradesheet[['buy_time', 'buy_price']].rename(columns={'buy_time': 'Date', 'buy_price': 'Price'})
    exits = tradesheet[['sell_time', 'sell_price']].rename(columns={'sell_time': 'Date', 'sell_price': 'Price'})
    
    entries.set_index('Date', inplace=True)
    exits.set_index('Date', inplace=True)
    
    colors = mpf.make_marketcolors(up='g', down='r', inherit=True)
    style1 = mpf.make_mpf_style(marketcolors=colors)
    
    plots = [
       mpf.make_addplot(data['ema_10'], color='blue'),
       mpf.make_addplot(data['ema_20'], color='orange'),
       mpf.make_addplot(data['vwma_20'], color='purple'),
       mpf.make_addplot(data['rsi_14'], panel=1, color='green', ylabel='RSI')
    ]
    
    fig, axs = mpf.plot(
        data,
        type='candle',
        style=style1,
        addplot=plots,
        volume=True,
        panel_ratios=(6,2),
        returnfig=True,
        title='Trading backtest TSLA',
        figscale=1.2
    )
    
    ax1 = axs[0]
    ax1.plot(entries.index, entries['Price'], '^', color='lime', markersize=10, label='Buy')
    ax1.plot(exits.index, exits['Price'], 'v', color='red', markersize=10, label='Sell')
    ax1.legend()
    
    plt.show()

