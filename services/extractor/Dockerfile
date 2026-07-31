# syntax=docker/dockerfile:1
FROM python:3.11-slim AS build
WORKDIR /app
COPY pyproject.toml ./
COPY src/ ./src/
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir .

FROM python:3.11-slim
WORKDIR /app
COPY --from=build /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=build /usr/local/bin /usr/local/bin
ENV PYTHONUNBUFFERED=1 \
    PORT=8080
EXPOSE 8080
CMD ["uvicorn", "extractor.main:app", "--host", "0.0.0.0", "--port", "8080"]
