FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

ENV MODEL_PATH=/models/model.gguf \
    N_THREADS=4 \
    N_CTX=2048 \
    HOST=0.0.0.0 \
    PORT=8000

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
