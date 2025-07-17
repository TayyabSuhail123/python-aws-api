# ---------- Base image ----------
FROM python:3.11-slim

# ---------- Work directory ----------
WORKDIR /app

# ---------- Install dependencies ----------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---------- Copy source ----------
COPY . .

# ---------- Default ENV (override with --env-file) ----------
ENV LOG_LEVEL=INFO \
    AGENT_TIMEOUT=5

# ---------- Expose FastAPI port ----------
EXPOSE 8000

# ---------- Start app ---------
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
