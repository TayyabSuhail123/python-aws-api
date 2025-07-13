# 🏃‍♂️ Minimal Agent-Runner – Python API

Self-contained FastAPI service that launches **one agent at a time** and exposes
REST endpoints to start / monitor runs. Designed as a foundation for automating
insurance workflows yet small enough to grok in minutes.

---

## 🎯 Why This Exists
- **Challenge goal:** Prove the ability to structure async Python, enforce a
  singleton task-runner, and reason about scalability, observability, and
  security.
- **Scope:** Focus on clean architecture & documentation; (Terraform,
  infra in another repo)

---

## 📐 High-Level Architecture
```text
┌────────────┐  POST /agents/run   ┌──────────────┐
│  Client     │ ───────────────▶  │  FastAPI app │
└────────────┘                    │              │
        ▲                         │  asyncio.Lock│  (prevents concurrent runs)
        │  GET /agents/status     │              │
        └───────────────◀──────── │  Agent Pool  │
                                  └──────┬───────┘
                                         │
                               ┌──────────▼─────────┐
                               │  BaseAgent (ABC)   │
                               │  • run() async     │
                               │  • logs JSON       │
                               └───────┬────────────┘
                   ┌──────────────────┴──────────────────┐
                   │                                     │
       DocumentExtractorAgent                PolicyCheckerAgent
```

*One `asyncio.Lock` gatekeeps the execution queue.  
Logs flow to stdout in structured JSON.*

---

## 🛣️ API Endpoints

| Method | Path | Purpose | Happy Response |
|--------|------|---------|----------------|
| `POST` | `/agents/run` | Kick off a run | `202 Accepted`, JSON `{run_id}` |
| `GET`  | `/agents/status/{run_id}` | Poll status / result | `200 OK`, JSON with `state` and `result` |

### Request Payload

```jsonc
{
  "agent_type": "document-extractor", // or "policy-checker"
  "user_id": "9b64a3a7-f8e4-4f06-8e57-73b50b042f29"
}
```

---

## 🤖 Agent Lifecycle

1. **START** – logs `"Hello, I am a <agent-type> agent for <user-id>"`.
2. **EXECUTION** – sleeps 5 s (placeholder for real work).
3. **COMPLETE** – logs completion message.  
   *Policy-checker* additionally logs a random `"approved"` / `"rejected"`.
4. **States** exposed to clients: `PENDING` → `RUNNING` → `DONE` or `ERROR`.

---

## 🚦 Single-Run Constraint & Trade-offs

| Why chosen             | Scaling path                                   | Drawbacks |
|------------------------|------------------------------------------------|-----------|
| *Business rule:* ensure deterministic access to single external mutexed resource (e.g., expensive licence).<br>*Simplicity:* one in-process lock, no DB needed. | • Swap `asyncio.Lock` for a distributed lock (Redis, DynamoDB Lease).<br>• Spin multiple runner replicas behind a queue and let the lock span pods.<br>• Or just allow concurrency once resource limits removed. | • Throughput = 1 → latency spikes.<br>• App instance becomes single point of contention.<br>• Not horizontally scalable without redesign.|

Rejected requests return **`409 Conflict`** with JSON:

```json
{"detail": "An agent is already running, please retry later"}
```

---

## 🧯 Error Handling Strategy

| Scenario                       | Handling                                                  |
|--------------------------------|-----------------------------------------------------------|
| Unknown `agent_type`           | `400 Bad Request` + log `"Unsupported agent_type"`        |
| Agent code raises exception    | catch, log stack, mark run as `ERROR`, respond `500`      |
| Multiple run attempt while busy| `409 Conflict` (see above)                                |

> Faults are isolated; the server keeps serving subsequent requests.

---

## 🔍 Structured Logging

All logs use `structlog` → JSON with keys: `timestamp`, `level`, `event`,
`agent_type`, `user_id`, `run_id`. Example:

```json
{"timestamp":"2025-07-13T14:01:12Z","level":"info",
 "event":"agent_start","agent_type":"document-extractor",
 "user_id":"9b64...","run_id":"c4ff..."}
```

*These flow straight into CloudWatch / Datadog without parsing gymnastics.*

---



## 🧪 Testing Approach



Run all:

```bash
pytest -q
```

## ⚡ Quick Start

```bash
git clone https://github.com/TayyabSuhail123/python-aws-api.git
cd python-aws-api
pip install -r requirements.txt
cp .env.example .env          # tweak LOG_LEVEL etc.
uvicorn main:app --reload     # → http://localhost:8000
```

### Docker

```bash
docker build -t agent-runner .
docker run -p 8000:8000 --env-file .env agent-runner
```

---


