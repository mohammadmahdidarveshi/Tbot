# Gold EMA Telegram Alert

A Telegram bot that monitors `XAUUSD=X` (gold) from Yahoo Finance. It sends one alert when the price range of a completed candle touches EMA(20): `Low <= EMA20 <= High`.

## Deploy to Render

This repository includes `render.yaml` and a `Dockerfile` for a continuous Background Worker.

1. Create a Render account and select **New > Blueprint**.
2. Connect this GitHub repository.
3. Add these secret environment variables in Render:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
4. Deploy.

The service will then run independently of your computer. Do not commit a real `.env` file.

## Local setup

Copy `.env.example` to `.env`, fill in the Telegram token and chat ID, then run:

```sh
python -m pip install -r requirements.txt
python gold_sma_alert.py
```

Configuration defaults: XAU/USD, 1-hour candles, EMA(20), checking every five minutes.
