FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY gold_sma_alert.py ./

CMD ["python", "-u", "gold_sma_alert.py"]
