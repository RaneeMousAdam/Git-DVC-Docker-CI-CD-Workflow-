FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install --prefix=/install --no-cache-dir -r requirements.txt


FROM python:3.11-slim AS runtime

LABEL org.opencontainers.image.title="safe-health-risk-model"
LABEL org.opencontainers.image.description="Patient Risk Prediction Service"
LABEL org.opencontainers.image.vendor="Safe-Health Inc."

RUN groupadd -r safehealth && useradd -r -g safehealth safehealth

WORKDIR /app

COPY --from=builder /install /usr/local

COPY scripts/      ./scripts/
COPY data/         ./data/
COPY model/        ./model/

RUN chown -R safehealth:safehealth /app

USER safehealth

ENV DATA_PATH=/app/data/patients.csv \
    MODEL_PATH=/app/model/risk_model.pkl \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python scripts/check_data.py || exit 1

ENTRYPOINT ["python", "scripts/check_data.py"]
