import pandas as pd
import yfinance as yf
import feedparser
import json
import os
from datetime import datetime, timezone
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

# --- CONFIGURATION ---
tickers = ["AAPL", "MSFT", "TSLA"]
startdate = "2021-01-01"
buythresh = 0.60
sellthresh = 0.40
trainratio = 0.80
rssurl = "https://feeds.finance.yahoo.com/rss/2.0/headline?s=AAPL,MSFT,TSLA&region=US&lang=en-US"

# --- DATA DOWNLOAD ---
print("Downloading market data...")
analyzer = SentimentIntensityAnalyzer()
# threads=False prevents the 'database is locked' error in Python 3.14
raw = yf.download(tickers, start=startdate, progress=False, group_by="ticker", threads=False)

rows = []
for t in tickers:
    try:
        if len(tickers) == 1:
            tmp = raw.reset_index()
        else:
            if t not in raw.columns.get_level_values(0):
                continue
            tmp = raw[t].reset_index()
        
        tmp["ticker"] = t
        tmp = tmp.rename(columns={"Date": "dt"})
        rows.append(tmp[["dt", "ticker", "Close"]])
    except Exception as e:
        print(f"Skipping {t} due to error: {e}")

if not rows:
    print("Critical Error: No data could be downloaded.")
    exit()

df = pd.concat(rows, ignore_index=True)
df["dt"] = pd.to_datetime(df["dt"])
df = df.sort_values(["dt", "ticker"]).copy()

# --- FEATURE ENGINEERING ---
df["returnday1"] = df.groupby("ticker")["Close"].pct_change(1)
df["fwdret"] = df.groupby("ticker")["Close"].shift(-1) / df["Close"] - 1.0
df["yup"] = (df["fwdret"] > 0).astype(int)

# --- SENTIMENT ANALYSIS ---
print("Fetching news headlines...")
feed = feedparser.parse(rssurl)
newsrows = []
for e in getattr(feed, "entries", []):
    title = getattr(e, "title", "")
    titlel = title.lower()
    
    dt = None
    for key in ["publishedparsed", "updatedparsed"]:
        t = getattr(e, key, None)
        if t:
            dt = datetime(*t[:6], tzinfo=timezone.utc).date()
            break
    if dt is None:
        dt = datetime.now(timezone.utc).date()

    sent = analyzer.polarity_scores(title)["compound"]
    matched = []
    if "apple" in titlel or "aapl" in titlel: matched.append("AAPL")
    if "microsoft" in titlel or "msft" in titlel: matched.append("MSFT")
    if "tesla" in titlel or "tsla" in titlel: matched.append("TSLA")

    for tkr in matched:
        newsrows.append({"dt": dt, "ticker": tkr, "sentiment": sent})

news = pd.DataFrame(newsrows)
if news.empty:
    agg = pd.DataFrame(columns=["dt", "ticker", "newscount", "newssent"])
else:
    agg = news.groupby(["dt", "ticker"], as_index=False).agg(
        newscount=("sentiment", "count"),
        newssent=("sentiment", "mean"),
    )

df["dtdate"] = df["dt"].dt.date
df = df.merge(agg, left_on=["dtdate", "ticker"], right_on=["dt", "ticker"], how="left", suffixes=('', '_y'))
df["newscount"] = df["newscount"].fillna(0).astype(int)
df["newssent"] = df["newssent"].fillna(0.0)
df = df.dropna(subset=["returnday1", "yup"]).copy()

# --- MACHINE LEARNING ---
features = ["returnday1", "newscount", "newssent"]
X = df[features]
y = df["yup"]

splitidx = int(len(df) * trainratio)
Xtrain, Xtest = X.iloc[:splitidx], X.iloc[splitidx:]
ytrain, ytest = y.iloc[:splitidx], y.iloc[splitidx:]

model = LogisticRegression(max_iter=500)
model.fit(Xtrain, ytrain)

# --- PREDICTIONS & EXPORT ---
latest = df.sort_values(["ticker", "dt"]).groupby("ticker", as_index=False).tail(1).copy()
latest["probup"] = model.predict_proba(latest[features])[:, 1]

def get_signal(p):
    if p >= buythresh: return "BUY"
    if p <= sellthresh: return "SELL"
    return "HOLD"

latest["signal"] = latest["probup"].apply(get_signal)

# Prepare JSON for React Frontend
market_data_export = {}
for tkr in tickers:
    tkr_df = df[df['ticker'] == tkr].tail(15)
    tkr_latest = latest[latest['ticker'] == tkr].iloc[0]
    
    # Logic for UI prediction line: if BUY, predict +2%, if SELL -2%, else flat
    last_price = float(tkr_df['Close'].iloc[-1])
    if tkr_latest['signal'] == "BUY":
        pred_price = last_price * 1.02
    elif tkr_latest['signal'] == "SELL":
        pred_price = last_price * 0.98
    else:
        pred_price = last_price

    market_data_export[tkr] = {
        "labels": tkr_df['dt'].dt.strftime('%b %d').tolist(),
        "historical": tkr_df['Close'].round(2).tolist(),
        "predicted": round(pred_price, 2),
        "signal": tkr_latest['signal'],
        "confidence": round(float(tkr_latest['probup']) * 100, 1),
        "sentiment": "Positive" if tkr_latest['newssent'] > 0 else "Neutral/Negative"
    }

# Save the file to the 'src' directory so React can find it
file_path = "C:/Users/alist/ai-finance-ui/src/marketData.json" 
with open(file_path, 'w') as f:
    json.dump(market_data_export, f, indent=2)

print(f"✅ Success! Data exported to {file_path}")
print(latest[["ticker", "probup", "signal"]])