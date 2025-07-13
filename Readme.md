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
        └───────────────◀──────── │  Agents      │
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

## 🚀 Why **FastAPI**?

| Feature                     | Benefit                                                                 |
|----------------------------|-------------------------------------------------------------------------|
| **Async-first design**     | Native `async`/`await` support for high-throughput non-blocking ops     |
| **Automatic OpenAPI docs** | FastAPI auto-generates an OpenAPI 3 spec + Swagger UI with no setup     |
| **Built-in Swagger UI**    | Available at [http://localhost:8080/docs](http://localhost:8080/docs)   |
| **Manual testing support** | Easily send POST/GET requests through browser without extra tools       |
| **Type safety**            | Request/response validation using Pydantic + Python typing              |

> Open `http://localhost:8080/docs` to interactively:
> - Trigger a new agent run (`POST /agents/run`)
> - Poll the agent’s status (`GET /agents/status/{run_id}`)
> - See request and response schemas instantly

This makes the API self-documenting and user-friendly for developers and testers

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


---

## 🛠️ CI/CD Pipeline (GitHub Actions)

This project uses a GitHub Actions workflow (`.github/workflows/docker-ecr.yml`) to build, test, scan, and push the Docker image to **AWS ECR** on every push to the `main` branch.

### 🧩 Steps Explained

| Step | Description |
|------|-------------|
| ✅ **Checkout code**         | Fetches the latest commit from `main` |
| 🐍 **Set up Python**         | Uses Python 3.10 |
| 📦 **Install dependencies**  | Installs project packages from `requirements.txt` |
| 🧪 **Run tests**             | Executes all `pytest` test cases. The build **fails if any test fails** |
| 🔐 **Configure AWS**         | Authenticates using GitHub secrets and sets AWS region |
| 🔑 **Login to ECR**          | Logs into Amazon ECR using AWS credentials |
| 🐳 **Build Docker image**    | Builds the image and tags it as:  
`<account_id>.dkr.ecr.eu-central-1.amazonaws.com/agent-runner-repo:latest` |
| 🛡️ **Trivy Security Scan**  | Scans the Docker image for **HIGH/CRITICAL** vulnerabilities and fails if found |
| 🚀 **Push to ECR**           | Pushes the image to your ECR repo if all checks pass |

> The pushed image is then used by the **ECS Fargate service** (provisioned in your separate Terraform repo) to deploy the backend container.

---

### 🔐 GitHub Secrets Used

| Secret Name              | Purpose                         |
|--------------------------|---------------------------------|
| `AWS_ACCESS_KEY_ID`      | Access key for ECR push         |
| `AWS_SECRET_ACCESS_KEY`  | Secret key for ECR push         |

---

### 🚦 Trigger

This workflow is configured with **`workflow_dispatch`**, meaning it only runs when you launch it manually:

1. Go to your repository’s **Actions** tab.
2. Select **“Build, Test, Scan, and Push to ECR”**.
3. Click **“Run workflow”**, choose the branch (default is `main`), and hit **Run**.

Because it’s manual, edits to docs or README files no longer kick off the pipeline to push to ECR.

⚠️ **Note on Image Tagging**

For demo purposes, this pipeline always builds and pushes the Docker image with the `:latest` tag:

While convenient for quick iteration and manual testing, **using `latest` in production is strongly discouraged**.

### ❌ Problems with `latest` in production:
- No version pinning = no rollback capability
- Makes deployments non-reproducible
- Not a secure practise to use latest tag as an attacker may gain acces and deploy another latest version.

### ✅ Production Best Practice:
Tag every image with a unique version — typically the Git SHA or a semver:
```bash
docker tag agent-runner:abc123 <repo>:abc123

```

### 🔐 Least-Privilege IAM Setup

A dedicated IAM user was created **only** for CI/CD pushes to ECR:

1. **User name**: `github-inca-CI`
2. **Access keys**: stored as GitHub Secrets  
   - `AWS_ACCESS_KEY_ID`  
   - `AWS_SECRET_ACCESS_KEY`
3. **Attached policy** minimum permissions for the demo (Can be further grained down)


## ✅ TODO – Next Improvements

These enhancements are planned to move from demo-grade to production-grade setup:

- 🔀 **Separate branches per environment** (e.g. `dev`, `staging`, `prod`)  
- ✅ **Merge Requests with approval required**  
  - Only approved MRs to `main` will trigger a CI pipeline that builds and pushes the image to ECR  
- 🏷️ **Replace `:latest` tag with versioned tags**  
  - Git SHA or release versions will be used  
  - Enables proper rollback and traceability  
- 🔐 **Secrets management with Vault**  
  - GitHub secrets will be replaced by a centralized **HashiCorp Vault setup**  
  - Each environment will have **isolated access policies**  
  - Prevents secrets from leaking across stages or services

These changes will help establish a secure, auditable, and production-ready delivery pipeline.


## 🤖 AI Assistance in This Project

To accelerate development and maintain clarity under time constraints, this project leveraged **AI-assisted workflows** for:

- 📄 **Documentation drafting**: Accelerated README creation and structured formatting  
- ⚙️ **Architecture design feedback**: Validated initial architecture choices and suggested scalability trade-offs  
- 🐍 **Python error troubleshooting**: Helped debug async code and refine logging structure  
- 📦 **CI/CD pipeline planning**: Assisted in planning a secure, minimal AWS deployment strategy via GitHub Actions  

All decisions were critically reviewed, and code was manually refined to ensure correctness and clarity.  
AI was treated as a **collaborator**, not an autopilot.
