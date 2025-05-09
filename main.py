import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import smtplib
from email.mime.text import MIMEText
import os

# === USER INPUT ===
TICKER = input("Enter stock ticker (e.g., AAPL): ").upper()
START_DATE = input("Enter start date (YYYY-MM-DD): ")
END_DATE = input("Enter end date (YYYY-MM-DD): ")

SHORT_WINDOW = 50
LONG_WINDOW = 200

# === DOWNLOAD DATA ===
data = yf.download(TICKER, start=START_DATE, end=END_DATE)[['Close']].dropna()

# === INDICATORS ===
data['SMA50'] = data['Close'].rolling(SHORT_WINDOW).mean()
data['SMA200'] = data['Close'].rolling(LONG_WINDOW).mean()

data['20_MA'] = data['Close'].rolling(20).mean()
data['20_STD'] = data['Close'].rolling(20).std()
data['UpperBand'] = data['20_MA'] + (2 * data['20_STD'])
data['LowerBand'] = data['20_MA'] - (2 * data['20_STD'])

# === SIGNALS ===
data['Signal'] = 0
data['Signal'][SHORT_WINDOW:] = np.where(
    data['SMA50'][SHORT_WINDOW:] > data['SMA200'][SHORT_WINDOW:], 1, 0)
data['Position'] = data['Signal'].diff()

# === EMAIL ALERT FUNCTION ===
def send_email_alert(signal_type, date, price):
    sender = "your_email@example.com"
    receiver = "receiver_email@example.com"
    subject = f"{signal_type} Alert for {TICKER}"
    body = f"{signal_type} signal for {TICKER} on {date.date()} at price ${price:.2f}"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = receiver

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender, "your_email_password")
            server.send_message(msg)
        print(f"Sent {signal_type} alert for {date.date()}")
    except Exception as e:
        print("Email sending failed:", e)

# === TRIGGER EMAIL ALERTS (Optional) ===
for date, row in data.iterrows():
    if row['Position'] == 1:
        send_email_alert("Buy", date, row['Close'])
    elif row['Position'] == -1:
        send_email_alert("Sell", date, row['Close'])

# === VISUALIZE STRATEGY ===
plt.figure(figsize=(14, 8))
plt.plot(data['Close'], label='Close Price', alpha=0.5)
plt.plot(data['SMA50'], label='SMA50')
plt.plot(data['SMA200'], label='SMA200')
plt.plot(data['UpperBand'], label='Upper Bollinger Band', linestyle='--', color='gray')
plt.plot(data['LowerBand'], label='Lower Bollinger Band', linestyle='--', color='gray')
plt.fill_between(data.index, data['LowerBand'], data['UpperBand'], color='gray', alpha=0.1)
plt.scatter(data.index[data['Position'] == 1], data['Close'][data['Position'] == 1],
            label='Buy Signal', marker='^', color='green', s=100)
plt.scatter(data.index[data['Position'] == -1], data['Close'][data['Position'] == -1],
            label='Sell Signal', marker='v', color='red', s=100)
plt.title(f'{TICKER} Strategy: SMA & Bollinger Bands')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("strategy_plot.png")
plt.show()

# === BACKTEST ===
data['Returns'] = data['Close'].pct_change()
data['Strategy'] = data['Signal'].shift(1) * data['Returns']
cumulative_returns = (1 + data['Strategy']).cumprod()
cumulative_benchmark = (1 + data['Returns']).cumprod()

plt.figure(figsize=(12, 6))
plt.plot(cumulative_returns, label='Strategy Returns')
plt.plot(cumulative_benchmark, label='Benchmark Returns')
plt.title(f'{TICKER} Strategy vs. Buy & Hold')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("backtest_plot.png")
plt.show()

# === METRICS ===
total_return = cumulative_returns[-1] - 1
volatility = data['Strategy'].std() * np.sqrt(252)
sharpe_ratio = data['Strategy'].mean() / data['Strategy'].std() * np.sqrt(252)

print(f"\nPerformance Summary for {TICKER}:\n")
print(f"Total Strategy Return: {total_return:.2%}")
print(f"Annualized Volatility: {volatility:.2%}")
print(f"Sharpe Ratio: {sharpe_ratio:.2f}")

# === EXPORT TO EXCEL ===
output_path = f"{TICKER}_strategy_report.xlsx"
data.to_excel(output_path)
print(f"\nReport exported to {output_path}")
