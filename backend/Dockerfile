# syntax=docker/dockerfile:1
# Backend — FastAPI API Gateway served by Uvicorn.
# Installs the hatch project (both `_common` and `gateway` import packages) plus the
# sqlite extra, then runs the app factory `gateway.main:app`.

FROM python:3.14-slim AS runtime
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Copy the whole backend context (packages declared in pyproject:
#   packages = ["_common", "gateway"]) and install it.
COPY . .
RUN pip install --upgrade pip && pip install ".[sqlite]"

EXPOSE 8000
# Uvicorn imports the app factory result `app` from gateway.main (installed package).
CMD ["uvicorn", "gateway.main:app", "--host", "0.0.0.0", "--port", "8000"]
