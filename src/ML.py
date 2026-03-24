def run_model():
    print("🚀 MODEL STARTED")

    import os, time, json, requests
    import pandas as pd
    from datetime import datetime
    from sklearn.linear_model import LogisticRegression

    tickers = ["AAPL", "MSFT", "TSLA"]
    buythresh, sellthresh = 0.60, 0.40

    apikey = os.getenv("ALPHAVANTAGE_API_KEY") or "PASTE_YOUR_KEY_HERE"

    baseurl = "https://www.alphavantage.co/query"
    sleepsecs = 1

    file_path = "./src/marketData.json"

    # =========================
    # 📊 FETCH PRICE DATA
    # =========================
    print("📊 Fetching price data...")

    allrows = []
    for i, tkr in enumerate(tickers):
        url = f"{baseurl}?function=TIME_SERIES_DAILY&symbol={tkr}&outputsize=compact&apikey={apikey}"
        data = requests.get(url).json()

        if "Time Series (Daily)" not in data:
            print(f"❌ API error for {tkr}:", data)
            return

        for dt_str, vals in data["Time Series (Daily)"].items():
            allrows.append({
                "dt": dt_str,
                "ticker": tkr,
                "Close": float(vals["4. close"])
            })

        if i < len(tickers) - 1:
            time.sleep(sleepsecs)

    df = pd.DataFrame(allrows)

    if df.empty:
        print("❌ No price data fetched")
        return

    print(f"✅ Price rows: {len(df)}")

    df["dt"] = pd.to_datetime(df["dt"])
    df = df.sort_values(["ticker", "dt"])

    # =========================
    # ⚙️ FEATURES
    # =========================
    df["returnday1"] = df.groupby("ticker")["Close"].pct_change(1)
    df["returnday5"] = df.groupby("ticker")["Close"].pct_change(5)
    df["fwdret"] = df.groupby("ticker")["Close"].shift(-1) / df["Close"] - 1
    df["yup"] = (df["fwdret"] > 0).astype(int)

    # =========================
    # 📰 NEWS
    # =========================
    print("📰 Fetching news...")

    newsurl = f"{baseurl}?function=NEWS_SENTIMENT&tickers={','.join(tickers)}&apikey={apikey}"
    newsdata = requests.get(newsurl).json()

    newsrows = []
    for item in newsdata.get("feed", []):
        try:
            dt = datetime.strptime(item["time_published"][:8], "%Y%m%d").date()
        except:
            continue

        for tsent in item.get("ticker_sentiment", []):
            newsrows.append({
                "dt": dt,
                "ticker": tsent.get("ticker"),
                "sentiment": float(tsent.get("ticker_sentiment_score", 0))
            })

    news = pd.DataFrame(newsrows)

    if news.empty:
        print("⚠️ No news data found")
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

    # =========================
    # 🔗 MERGE
    # =========================
    df["dtdate"] = df["dt"].dt.date

    df = df.merge(
        agg,
        left_on=["dtdate", "ticker"],
        right_on=["dt", "ticker"],
        how="left"
    )

    df["newscount"] = df["newscount"].fillna(0)
    df["newssent"] = df["newssent"].fillna(0)
    df["newssent3day"] = df["newssent3day"].fillna(0)

    df = df.dropna(subset=["returnday1", "returnday5"])

    # =========================
    # 🤖 TRAIN MODEL PER STOCK
    # =========================
    print("🤖 Training models per stock...")

    features = ["returnday1", "returnday5", "newscount", "newssent", "newssent3day"]

    models = {}

    for tkr in tickers:
        sub = df[df["ticker"] == tkr]

        X = sub[features]
        y = sub["yup"]

        model = LogisticRegression(max_iter=500)
        model.fit(X, y)

        models[tkr] = model

    # =========================
    # 📈 PREDICTIONS
    # =========================
    latest = df.groupby("ticker").tail(1).copy()

    latest["probup"] = [
        models[row["ticker"]].predict_proba(
            row[features].values.reshape(1, -1)
        )[0][1]
        for _, row in latest.iterrows()
    ]

    def getsignal(p):
        if p >= buythresh:
            return "BUY"
        if p <= sellthresh:
            return "SELL"
        return "HOLD"

    latest["signal"] = latest["probup"].apply(getsignal)

    # =========================
    # 📦 EXPORT
    # =========================
    print("💾 Saving JSON...")

    export = {}

    for tkr in tickers:
        tkr_df = df[df["ticker"] == tkr].tail(15)

        if tkr_df.empty:
            continue

        row = latest[latest["ticker"] == tkr].iloc[0]
        last_price = tkr_df["Close"].iloc[-1]

        # 🔥 Continuous prediction (no more flat lines)
        pred_price = last_price * (1 + (row["probup"] - 0.5) * 0.5)

        export[tkr] = {
            "labels": tkr_df["dt_x"].dt.strftime("%b %d").tolist(),
            "historical": tkr_df["Close"].round(2).tolist(),
            "predicted": round(pred_price, 2),
            "signal": row["signal"],
            "confidence": round(row["probup"] * 100, 1),
            "sentiment": "Positive" if row["newssent"] > 0 else "Neutral/Negative",
        }
        print(latest[["ticker", "probup"]])

    with open(file_path, "w") as f:
        json.dump(export, f, indent=2)

    print("✅ Updated marketData.json")


# 🚀 RUN
if __name__ == "__main__":
    run_model()