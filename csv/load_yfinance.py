import yfinance as yf
import pandas as pd

# Download stock data
symbols = [
    # Tech Giants
    'AAPL', 'MSFT', 'GOOGL', 'TSLA', 'META', 'NVDA', 'AMZN',
    
    # Cloud/SaaS
    'SALESFORCE', 'ADBE', 'CRM', 'OKTA', 'ZM', 'NFLX',
    
    # Financials
    'JPM', 'BAC', 'GS', 'WFC', 'BLK', 'SCHW',
    
    # Healthcare
    'JNJ', 'UNH', 'PFE', 'ABBV', 'MRK', 'LLY',
    
    # Energy
    'XOM', 'CVX', 'COP', 'MPC', 'PSX',
    
    # Consumer
    'WMT', 'TGT', 'COST', 'HD', 'LOW', 'MCD',
    
    # Industrials
    'BA', 'CAT', 'GE', 'MMM', 'RTX', 'LMT',
    
    # Semiconductors
    'AMD', 'INTC', 'QCOM', 'AVGO', 'MU', 'ASML',
    
    # ETFs (diversified)
    'SPY', 'QQQ', 'IWM', 'EEM', 'GLD', 'TLT'
]


import yfinance as yf
import pandas as pd
import time

symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'META']

print(f"Downloading {len(symbols)} symbols...")
all_data = []

for symbol in symbols:
    print(f"  {symbol}...", end=" ", flush=True)
    
    try:
        # Download
        df = yf.download(symbol, start="2023-01-01", progress=False)
        
        # Flatten MultiIndex columns
        df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
        
        # Reset index (Date becomes a column)
        df.reset_index(inplace=True)
        df['Symbol'] = symbol
        
        # Select columns
        df = df[['Date', 'Symbol', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']]
        
        all_data.append(df)
        print(f"✓ ({len(df)} rows)")
        
    except Exception as e:
        print(f"✗ {e}")
    
    time.sleep(0.3)

if all_data:
    combined = pd.concat(all_data, ignore_index=True)
    combined.to_csv('all_stocks.csv', index=False)
    print(f"\n✅ Saved all_stocks.csv ({len(combined):,} rows)")
    print(combined.head())
else:
    print("\n❌ No data!")
EOF