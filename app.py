import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st

st.set_page_config(page_title="Stock Strategy Analyzer", layout="wide")

# Sidebar Inputs
st.sidebar.title("📊 Strategy Parameters")
ticker = st.sidebar.text_input("Stock Ticker", "AAPL").upper()
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2022-01-01"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("2023-01-01"))
short_window = st.sidebar.slider("Short Window (SMA)", 10, 100, 50)
long_window = st.sidebar.slider("Long Window (SMA)", 20, 300, 200)

# Load data
@st.cache_data
def load_data(ticker, start, end):
    df = yf.download(ticker, start=start, end=end)
    return df[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()

data = load_data(ticker, start_date, end_date)

# Indicators
data['SMA_short'] = data['Close'].rolling(short_window).mean()
data['SMA_long'] = data['Close'].rolling(long_window).mean()

# RSI
delta = data['Close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
rs = gain / loss
data['RSI'] = 100 - (100 / (1 + rs))

# MACD
ema12 = data['Close'].ewm(span=12, adjust=False).mean()
ema26 = data['Close'].ewm(span=26, adjust=False).mean()
data['MACD'] = ema12 - ema26
data['Signal_Line'] = data['MACD'].ewm(span=9, adjust=False).mean()

# Bollinger Bands
data['BB_Mid'] = data['Close'].rolling(window=20).mean()
data['BB_Upper'] = data['BB_Mid'] + 2 * data['Close'].rolling(window=20).std()
data['BB_Lower'] = data['BB_Mid'] - 2 * data['Close'].rolling(window=20).std()

# Strategy signals
data['Signal'] = 0
data['Signal'][short_window:] = np.where(data['SMA_short'][short_window:] > data['SMA_long'][short_window:], 1, 0)
data['Position'] = data['Signal'].diff()

# Plot chart
st.title(f"📈 {ticker} Strategy Dashboard")

fig, ax = plt.subplots(figsize=(14, 6))
ax.plot(data['Close'], label='Close Price', alpha=0.6)
ax.plot(data['SMA_short'], label=f'SMA {short_window}', linestyle='--')
ax.plot(data['SMA_long'], label=f'SMA {long_window}', linestyle='--')
ax.fill_between(data.index, data['BB_Upper'], data['BB_Lower'], color='gray', alpha=0.2, label='Bollinger Bands')
ax.scatter(data.index[data['Position'] == 1], data['Close'][data['Position'] == 1], label='Buy', marker='^', color='green')
ax.scatter(data.index[data['Position'] == -1], data['Close'][data['Position'] == -1], label='Sell', marker='v', color='red')
ax.legend()
ax.set_title(f"{ticker} Strategy with Indicators")
ax.grid()
st.pyplot(fig)

# Portfolio backtest
initial_cash = 10000
data['Daily Return'] = data['Close'].pct_change()
data['Strategy Return'] = data['Daily Return'] * data['Signal'].shift(1)
data['Portfolio Value'] = (1 + data['Strategy Return']).cumprod() * initial_cash

st.subheader("💰 Portfolio Equity Curve")
st.line_chart(data[['Portfolio Value']])

# Metrics
cumulative_return = (1 + data['Strategy Return']).cumprod().iloc[-1] - 1
max_drawdown = ((data['Close'] / data['Close'].cummax()) - 1).min()
total_trades = int(data['Position'].abs().sum())

st.subheader("📊 Strategy Metrics")
st.write(f"**Cumulative Return:** {cumulative_return:.2%}")
st.write(f"**Max Drawdown:** {max_drawdown:.2%}")
st.write(f"**Total Trades:** {total_trades}")

# Export to Excel
st.subheader("📁 Download Data")
excel_filename = f"{ticker}_strategy.xlsx"
to_export = data.copy()
to_export.index.name = "Date"
st.download_button("Download Excel", to_export.to_csv().encode("utf-8"), file_name=excel_filename)

# Earnings calendar
st.subheader("📅 Upcoming Earnings")
try:
    earnings = yf.Ticker(ticker).calendar
    st.dataframe(earnings.T)
except:
    st.write("No earnings data available.")