import json
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import yfinance as yf


# 銘柄コードと会社名
with open(
    "stocks.json",
    encoding="utf-8"
) as f:
    stocks = json.load(f)

rows = []

for code, name in stocks.items():
    try:
        df = yf.download(
            code,
            period="1y",
            auto_adjust=True,
            progress=False,
        )

        # yfinanceのMultiIndex対策
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # 欠損行を除外
        df = df.dropna(subset=["Close", "Volume"])

        # データ不足対策
        if df.empty or len(df) < 75:
            print(f"{code}: データ不足")
            continue

        # 指標
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

        above_ma25 = close > ma25
        ma25_above_ma75 = ma25 > ma75
        volume_ok = vol_ratio > 1.0
        near_high_ok = near_high > 0.90

        score = sum([
            above_ma25,
            ma25_above_ma75,
            volume_ok,
            near_high_ok,
        ])

        # 直近90営業日分のチャートデータ
        history = []

        for date, row in df.tail(90).iterrows():
            history_item = {
                "date": date.strftime("%Y-%m-%d"),
                "close": round(float(row["Close"]), 1),
            }

            # 移動平均がまだ計算できない期間はnullにする
            history_item["ma25"] = (
                round(float(row["MA25"]), 1)
                if pd.notna(row["MA25"])
                else None
            )

            history_item["ma75"] = (
                round(float(row["MA75"]), 1)
                if pd.notna(row["MA75"])
                else None
            )

            history.append(history_item)

        rows.append({
            "code": code,
            "name": name,
            "close": round(close, 1),
            "ma25": round(ma25, 1),
            "ma75": round(ma75, 1),
            "distance_ma25": round(
                (close / ma25 - 1) * 100,
                1,
            ),
            "distance_ma75": round(
                (close / ma75 - 1) * 100,
                1,
            ),
            "vol_ratio": round(vol_ratio, 2),
            "near_60d_high": round(near_high, 3),
            "score": int(score),
            "above_ma25": bool(above_ma25),
            "ma25_above_ma75": bool(ma25_above_ma75),
            "volume_ok": bool(volume_ok),
            "near_high_ok": bool(near_high_ok),
            "history": history,
        })

    except Exception as error:
        print(f"{code}: {error}")


# 点数、高値接近率、出来高比の順に並べる
rows.sort(
    key=lambda item: (
        item["score"],
        item["near_60d_high"],
        item["vol_ratio"],
    ),
    reverse=True,
)

updated_at = datetime.now(
    ZoneInfo("Asia/Tokyo")
).isoformat(timespec="seconds")

payload = {
    "updated_at": updated_at,
    "stocks": rows,
}

with open(
    "results.json",
    "w",
    encoding="utf-8",
) as file:
    json.dump(
        payload,
        file,
        ensure_ascii=False,
        indent=2,
        allow_nan=False,
    )

print(json.dumps(
    payload,
    ensure_ascii=False,
    indent=2,
    allow_nan=False,
))

print("\nresults.json saved.")
