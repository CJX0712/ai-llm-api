FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# llama-cpp-python：用官方预编译 CPU wheel，避免在镜像内源码编译（无需 cmake/gcc）
RUN pip install --no-cache-dir --only-binary=llama-cpp-python \
        llama-cpp-python \
        --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu

COPY app.py .

ENV MODEL_PATH=/models/model.gguf \
    N_THREADS=4 \
    N_CTX=2048 \
    HOST=0.0.0.0 \
    PORT=8000

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
