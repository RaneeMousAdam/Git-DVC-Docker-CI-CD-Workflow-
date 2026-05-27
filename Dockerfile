# =============================================================================
# Safe-Health Risk Model – Multi-stage Dockerfile
# Stage 1 (builder): compile/install all Python dependencies
# Stage 2 (runtime): minimal image with only what is needed at runtime
# =============================================================================

# ── Stage 1: builder ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install only the C-level build tools that heavy packages (numpy) need.
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install into an isolated prefix so we can copy just /install later.
RUN pip install --upgrade pip \
    && pip install --prefix=/install --no-cache-dir -r requirements.txt


# ── Stage 2: runtime ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

LABEL org.opencontainers.image.title="safe-health-risk-model"
LABEL org.opencontainers.image.description="Patient Risk Prediction Service"
LABEL org.opencontainers.image.vendor="Safe-Health Inc."

# Run as a non-root user for security.
RUN groupadd -r safehealth && useradd -r -g safehealth safehealth

WORKDIR /app

# Copy compiled dependencies from the builder stage.
COPY --from=builder /install /usr/local

# Copy application code.
COPY scripts/ ./scripts/

# Copy the dataset (present in the build context during CI after dvc pull,
# or directly from git when building locally).
COPY data/patients.csv ./data/patients.csv

# Create the model directory (model artefacts are mounted at runtime).
RUN mkdir -p ./model

RUN chown -R safehealth:safehealth /app

USER safehealth

ENV DATA_PATH=/app/data/patients.csv \
    MODEL_PATH=/app/model/risk_model.pkl \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python scripts/check_data.py || exit 1

ENTRYPOINT ["python", "scripts/check_data.py"]
