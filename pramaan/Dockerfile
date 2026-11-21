# Hosted checker / paid API. Builds the index at image build time.
#   docker build -t pramaan . && docker run -p 8000:8000 -e PRAMAAN_API_KEYS=key1,key2 pramaan
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends poppler-utils && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir ".[sync,pdf]" && pramaan --db /app/idx/sc.sqlite sync
ENV PRAMAAN_DB=/app/idx/sc.sqlite PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "pramaan serve --host 0.0.0.0 --port ${PORT}"]
