import yfinance as yf
import pandas as pd

# ==========================
# 監視銘柄
# ==========================
codes = [
    "5803.T",   # フジクラ
    "6526.T",   # ソシオネクスト
    "6227.T",   # AIメカテック
    "4413.T",   # ボードルア
    "5253.T",   # カバー
]

rows = []

for code in codes:

    try:
        df = yf.download(
            code,
            period="1y",
            auto_adjust=True,
            progress=False
        )

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        if len(df) < 75:
            continue

        # テクニカル指標
        df["MA25"] = df["Close"].rolling(25).mean()
        df["MA75"] = df["Close"].rolling(75).mean()
        df["VOL20"] = df["Volume"].rolling(20).mean()
        df["HIGH60"] = df["Close"].rolling(60).max()

        last = df.iloc[-1]

        close = float(last["Close"])
        ma25 = float(last["MA25"])
        ma75 = float(last["MA75"])
        vol_ratio = float(last["Volume"] / last["VOL20"])
        near_high = float(last["Close"] / last["HIGH60"])

        # スコア計算
        score = 0
        score += close > ma25
        score += ma25 > ma75
        score += vol_ratio > 1.0
        score += near_high > 0.90

        rows.append({
            "code": code,
            "close": round(close, 1),
            "ma25": round(ma25, 1),
            "ma75": round(ma75, 1),
            "distance_ma25(%)": round((close / ma25 - 1) * 100, 1),
            "distance_ma75(%)": round((close / ma75 - 1) * 100, 1),
            "vol_ratio": round(vol_ratio, 2),
            "near_60d_high": round(near_high, 3),
            "score": int(score),
            "above_ma25": close > ma25,
            "ma25_above_ma75": ma25 > ma75,
            "volume_ok": vol_ratio > 1.0,
            "near_high_ok": near_high > 0.90,
        })

    except Exception as e:
        print(code, e)

# ==========================
# DataFrame
# ==========================
result = pd.DataFrame(rows)

result = result.sort_values(
    by=["score", "near_60d_high", "vol_ratio"],
    ascending=False
)

print(result)

print("\n===== score >= 3 =====")
print(result[result["score"] >= 3])

# ==========================
# JSON保存（アプリ用）
# ==========================
result.to_json(
    "results.json",
    orient="records",
    force_ascii=False,
    indent=2
)

print("\nresults.json saved.")
