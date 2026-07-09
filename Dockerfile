# syntax=docker/dockerfile:1.7
FROM python:3.12-slim AS builder

WORKDIR /build
COPY --link pyproject.toml requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir uvicorn[standard] pydantic-settings prometheus-client

COPY --link . .
RUN pip install --no-cache-dir -e .


FROM python:3.12-slim AS runner

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      libgomp1 \
      libgl1-mesa-glx \
      libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -r app && useradd -r -g app -d /app app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /build/api /app/api
COPY --from=builder /build/research_agent /app/research_agent
COPY --from=builder /build/search_service /app/search_service
COPY --from=builder /build/download_service /app/download_service
COPY --from=builder /build/document_processing_service /app/document_processing_service
COPY --from=builder /build/knowledge_base /app/knowledge_base
COPY --link pyproject.toml /app/

WORKDIR /app
USER app

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
  CMD python -c "import http.client; c=http.client.HTTPConnection('localhost:8000'); c.request('GET','/api/v1/health'); r=c.getresponse(); exit(0 if r.status==200 else 1)"

CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*", "--timeout-keep-alive", "30"]
