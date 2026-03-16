def run_model():
import os
import time
import json
import requests
import pandas as pd
from datetime import datetime

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

tickers = ["AAPL", "MSFT", "TSLA"]

buythresh = 0.60
sellthresh = 0.40
trainratio = 0.80

apikey = os.getenv("ALPHAVANTAGE_API_KEY")
baseurl = "https://www.alphavantage.co/query"
sleepsecs = 12  
cachefile = "prices_cache.csv"

file_path = r"C:/Users/alist/ai-finance-ui/src/marketData.json"

if not apikey:
    print("Error: ALPHAVANTAGE_API_KEY not set.")
    exit()

print("Getting price data from Alpha Vantage...")

allrows = []
for i, tkr in enumerate(tickers):
    url = (
        f"{baseurl}?function=TIME_SERIES_DAILY"
        f"&symbol={tkr}&outputsize=compact&apikey={apikey}"
    )
    r = requests.get(url)
    data = r.json()

    ts = data.get("Time Series (Daily)", {})
    for dt_str, vals in ts.items():
        allrows.append({
            "dt": dt_str,
            "ticker": tkr,
            "Close": float(vals["4. close"])
        })
    if i < len(tickers) - 1:
        time.sleep(sleepsecs)

newdf = pd.DataFrame(allrows)
if newdf.empty:
    print("No price data received.")
    exit()

newdf["dt"] = pd.to_datetime(newdf["dt"])
newdf = newdf.sort_values(["ticker", "dt"])
if os.path.exists(cachefile):
    old = pd.read_csv(cachefile, parse_dates=["dt"])
    df = pd.concat([old, newdf], ignore_index=True)
else:
    df = newdf.copy()

df = df.drop_duplicates(subset=["dt", "ticker"]).sort_values(["ticker", "dt"]).reset_index(drop=True)
df.to_csv(cachefile, index=False)
df["returnday1"] = df.groupby("ticker")["Close"].pct_change(1)
df["returnday5"] = df.groupby("ticker")["Close"].pct_change(5)
df["fwdret"] = df.groupby("ticker")["Close"].shift(-1) / df["Close"] - 1.0
df["yup"] = (df["fwdret"] > 0).astype(int)
print("Getting news sentiment...")

time.sleep(sleepsecs)  # just to avoid rate limit after price calls

newsurl = (
    f"{baseurl}?function=NEWS_SENTIMENT"
    f"&tickers={','.join(tickers)}&sort=LATEST&limit=200&apikey={apikey}"
)
newsdata = requests.get(newsurl).json()

newsrows = []
feed = newsdata.get("feed", [])
for item in feed:
    tpub = item.get("time_published", "")
    if len(tpub) >= 8:
        dt = datetime.strptime(tpub[:8], "%Y%m%d").date()
    else:
        dt = datetime.utcnow().date()

    for tsent in item.get("ticker_sentiment", []):
        tkr = tsent.get("ticker")
        if tkr in tickers:
            try:
                score = float(tsent.get("ticker_sentiment_score", 0))
            except:
                score = 0.0
            newsrows.append({"dt": dt, "ticker": tkr, "sentiment": score})

news = pd.DataFrame(newsrows)

if news.empty:
    agg = pd.DataFrame(columns=["dt", "ticker", "newscount", "newssent", "newssent3day"])
else:
    agg = news.groupby(["dt", "ticker"], as_index=False).agg(
        newscount=("sentiment", "count"),
        newssent=("sentiment", "mean"),
    )
    agg = agg.sort_values(["ticker", "dt"])
    agg["newssent3day"] = agg.groupby("ticker")["newssent"].transform(
        lambda s: s.rolling(3).mean()
    )
df["dtdate"] = df["dt"].dt.date
df = df.merge(agg, left_on=["dtdate", "ticker"], right_on=["dt", "ticker"], how="left")

df["newscount"] = df["newscount"].fillna(0).astype(int)
df["newssent"] = df["newssent"].fillna(0.0)
df["newssent3day"] = df["newssent3day"].fillna(0.0)
df = df.dropna(subset=["returnday1", "returnday5", "yup"]).copy()
df = df.sort_values(["dt", "ticker"]).copy()

df = df.dropna(subset=["returnday1", "returnday5", "yup"]).copy()
X = df[features]
y = df["yup"].astype(int)

splitidx = int(len(df) * trainratio)
Xtrain, Xtest = X.iloc[:splitidx], X.iloc[splitidx:]
ytrain, ytest = y.iloc[:splitidx], y.iloc[splitidx:]

model = LogisticRegression(max_iter=500)
model.fit(Xtrain, ytrain)

pred = model.predict(Xtest)
acc = accuracy_score(ytest, pred)

baseline = [1] * len(ytest)
baselineacc = accuracy_score(ytest, baseline)

print(f"model accuracy:    {acc:.3f}")
print(f"baseline accuracy: {baselineacc:.3f}")
latest = df.sort_values(["ticker", "dt"]).groupby("ticker", as_index=False).tail(1).copy()
latest["probup"] = model.predict_proba(latest[features])[:, 1]

def getsignal(p):
    if p >= buythresh:
        return "BUY"
    if p <= sellthresh:
        return "SELL"
    return "HOLD"

latest["signal"] = latest["probup"].apply(getsignal)
export = {}
for tkr in tickers:
    tkr_df = df[df["ticker"] == tkr].tail(15)
    if tkr_df.empty:
        continue

    row = latest[latest["ticker"] == tkr].iloc[0]
    last_price = float(tkr_df["Close"].iloc[-1])
    if row["signal"] == "BUY":
        pred_price = last_price * 1.02
    elif row["signal"] == "SELL":
        pred_price = last_price * 0.98
    else:
        pred_price = last_price

    export[tkr] = {
        "labels": pd.to_datetime(tkr_df["dt"]).dt.strftime("%b %d").tolist(),
        "historical": tkr_df["Close"].round(2).tolist(),
        "predicted": round(pred_price, 2),
        "signal": row["signal"],
        "confidence": round(float(row["probup"]) * 100, 1),
        "sentiment": "Positive" if float(row["newssent"]) > 0 else "Neutral/Negative",
    }

try:
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w") as f:
        json.dump(export, f, indent=2)
    print("Saved JSON to:", file_path)
except Exception as e:
    return export
    print("Could not save JSON:", e)

print("\nSignals:")
print(latest[["ticker", "probup", "signal"]].to_string(index=False))
