"""Send a Telegram alert when XAU/USD touches its EMA(20)."""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

import pandas as pd
import yfinance as yf
from dotenv import load_dotenv

STATE_FILE = Path(".gold_ema_alert_state.json")


def setting(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if not value:
        raise RuntimeError(f"Missing required setting: {name}")
    return value


def load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state), encoding="utf-8")


def send_telegram(message: str) -> None:
    token = setting("TELEGRAM_BOT_TOKEN")
    chat_id = setting("TELEGRAM_CHAT_ID")
    endpoint = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urlencode({"chat_id": chat_id, "text": message}).encode("utf-8")
    with urlopen(endpoint, data=data, timeout=20) as response:
        result = json.loads(response.read().decode("utf-8"))
    if not result.get("ok"):
        raise RuntimeError(f"Telegram delivery failed: {result}")


def check_market() -> None:
    symbol = setting("SYMBOL", "XAUUSD=X")
    interval = setting("INTERVAL", "1h")
    period = int(setting("EMA_PERIOD", "20"))

    candles = yf.download(symbol, period="10d", interval=interval, progress=False, auto_adjust=False)
    if isinstance(candles.columns, pd.MultiIndex):
        candles.columns = candles.columns.get_level_values(0)
    if candles.empty or len(candles) < period + 2:
        raise RuntimeError("Insufficient data to calculate the EMA.")

    # The newest candle can still change, so only assess a closed candle.
    completed = candles.iloc[:-1].copy()
    completed["ema"] = completed["Close"].ewm(span=period, adjust=False).mean()
    candle = completed.iloc[-1]
    candle_time = str(completed.index[-1])
    high, low, close, ema = (float(candle[key]) for key in ("High", "Low", "Close", "ema"))
    touched = low <= ema <= high

    logging.info(
        "%s | high=%.2f low=%.2f close=%.2f ema%d=%.2f | touch=%s",
        candle_time, high, low, close, period, ema, touched,
    )
    if not touched:
        return

    state = load_state()
    alert_key = f"{symbol}:{interval}:{period}:{candle_time}"
    if state.get("last_alert") == alert_key:
        logging.info("This candle was already alerted.")
        return

    message = (
        "Gold EMA touch alert\n\n"
        f"Symbol: {symbol}\n"
        f"Timeframe: {interval}\n"
        f"Candle time: {candle_time}\n"
        f"EMA({period}): {ema:.2f}\n"
        f"High / Low: {high:.2f} / {low:.2f}\n"
        f"Close: {close:.2f}"
    )
    send_telegram(message)
    save_state({"last_alert": alert_key})
    logging.info("Alert sent.")


def main() -> None:
    load_dotenv()
    interval_seconds = int(setting("CHECK_EVERY_SECONDS", "300"))
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
    logging.info("Gold EMA alert bot started; checking every %s seconds.", interval_seconds)
    while True:
        try:
            check_market()
        except Exception:
            logging.exception("Market check failed")
        time.sleep(interval_seconds)


if __name__ == "__main__":
    main()
