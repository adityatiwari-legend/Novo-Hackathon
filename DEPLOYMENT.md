# Deployment & Operations Guide
## Agentic AI Co-Pilot for GxP IT System Management (Novo Nordisk Hackathon)

This guide provides end-to-end instructions for deploying the **GxP IT AI Co-Pilot** across different hosting environments, configured with **OpenRouter** and the **`nvidia/nemotron-3.5-lightning:free`** AI model.

---

## 1. Architecture Overview

```
                          ┌────────────────────────┐
                          │   End User / Auditor   │
                          └───────────┬────────────┘
                                      │ (HTTPS / HTTP)
                                      ▼
             ┌──────────────────────────────────────────────────┐
             │       Next.js 16+ Frontend (React 19, Turbo)     │
             │           Port 3000 (Vercel / Docker / Node)     │
             └────────────────────────┬─────────────────────────┘
                                      │ REST API Requests
                                      ▼
             ┌──────────────────────────────────────────────────┐
             │            FastAPI Backend (Python 3.11+)        │
             │           Port 8000 (Docker / Render / VM)       │
             └───────┬──────────────────────────┬───────────────┘
                     │                          │
        ┌────────────┴───────────┐   ┌──────────┴───────────────┐
        │  SQLite / PostgreSQL   │   │  OpenRouter AI Gateway   │
        │  Database (GXP Ledger) │   │  nvidia/nemotron-3.5-    │
        │  & Vector Embeddings   │   │  lightning:free          │
        └────────────────────────┘   └──────────────────────────┘
```

---

## 2. Environment Variables Configuration

Copy `.env.example` or create `.env` in the project root:

```env
# ==========================================
# OpenRouter AI Gateway Configuration
# ==========================================
OPENROUTER_API_KEY=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
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=nvidia/nemotron-3.5-lightning:free
AI_MODEL=nvidia/nemotron-3.5-lightning:free
AI_TEMPERATURE=0.1
AI_MAX_TOKENS=2048

# Legacy OpenAI Compatibility (points to OpenRouter)
OPENAI_API_KEY=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
OPENAI_MODEL=nvidia/nemotron-3.5-lightning:free

# ==========================================
# Database & File Storage
# ==========================================
DATABASE_URL=sqlite:///./gxp_copilot.db
VECTOR_STORE_PATH=data/vector_store
UPLOAD_DIR=data/uploads
SECRET_KEY=gxp-secret-key-novo-hackathon-2026-audit-ready-secure

# ==========================================
# Enterprise Integrations & Guardrails
# ==========================================
DEMO_MODE=true
MOCK_SERVICENOW=true
MOCK_VAULT=true
MOCK_IAM=true
MOCK_MONITORING=true
```

For the Frontend (`frontend/.env.local`):
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
# In production, replace localhost:8000 with your public backend domain:
# NEXT_PUBLIC_API_URL=https://api.yourdomain.com/api/v1
```

---

## 3. Deployment Option A: Docker Compose (Recommended for Judges / Cloud VM)

The simplest single-command deployment running PostgreSQL, FastAPI Backend, and Next.js Frontend together in containerized isolation.

### Prerequisites
- Docker Engine 20.10+
- Docker Compose 2.0+

### Steps:
```bash
# 1. Clone repository
git clone <your-repo-url>
cd "Novo Hackathon"

# 2. Launch all services
cd infra
docker compose up --build -d

# 3. Verify container health
docker compose ps
```

### Endpoints:
- **Frontend Dashboard**: `http://localhost:3000`
- **FastAPI API**: `http://localhost:8000/api/v1`
- **Swagger Documentation**: `http://localhost:8000/docs`
- **AI Health Telemetry**: `http://localhost:8000/api/v1/ai/health`

To stop the containers:
```bash
docker compose down
```

---

## 4. Deployment Option B: Cloud PaaS (Vercel + Render / Railway)

This is the standard modern stack for public hackathon demos with automatic SSL certificates.

### Step 1: Deploy Backend to Render or Railway
1. **Create New Web Service**:
   - Connect your GitHub repository.
   - Root directory: `./`
   - Build Command: `pip install -r backend/requirements.txt`
   - Start Command: `sh -c "python scripts/reset_demo.py && uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT"`
2. **Environment Variables on Render / Railway**:
   - `OPENROUTER_API_KEY`: `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`
   - `OPENROUTER_BASE_URL`: `https://openrouter.ai/api/v1`
   - `OPENROUTER_MODEL`: `nvidia/nemotron-3.5-lightning:free`
   - `AI_MODEL`: `nvidia/nemotron-3.5-lightning:free`
   - `DATABASE_URL`: `sqlite:///./gxp_copilot.db`
   - `SECRET_KEY`: `gxp-secret-key-novo-hackathon-2026-audit-ready-secure`
   - `DEMO_MODE`: `true`
3. Note your assigned backend URL (e.g. `https://gxp-backend.onrender.com`).

### Step 2: Deploy Frontend to Vercel
1. **Import Project into Vercel**:
   - Framework Preset: `Next.js`
   - Root Directory: `frontend`
2. **Set Environment Variable**:
   - `NEXT_PUBLIC_API_URL`: `https://gxp-backend.onrender.com/api/v1`
3. **Click Deploy**:
   - Vercel automatically builds and assigns a fast global CDN domain (e.g. `https://gxp-copilot.vercel.app`).

---

## 5. Deployment Option C: Linux Server (Ubuntu 22.04 / 24.04 LTS / AWS EC2)

For on-premise or cloud virtual machines:

### 1. System Packages Setup
```bash
sudo apt update && sudo apt install -y python3.11 python3.11-venv python3-pip nodejs npm nginx git
sudo npm install -g n && sudo n 20
```

### 2. Clone & Setup Project
```bash
git clone <your-repo-url> /opt/gxp-copilot
cd /opt/gxp-copilot

# Setup Python Virtual Environment
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt

# Configure .env
cp .env.example .env
nano .env   # Paste OPENROUTER_API_KEY and OPENROUTER_MODEL=nvidia/nemotron-3.5-lightning:free

# Seed Database & Ingest Lifecycle Docs
python scripts/reset_demo.py
```

### 3. Build Frontend
```bash
cd /opt/gxp-copilot/frontend
npm install
npm run build
```

### 4. Create Systemd Services

**Backend Service (`/etc/systemd/system/gxp-backend.service`)**:
```ini
[Unit]
Description=GxP IT AI Co-Pilot Backend
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/opt/gxp-copilot
ExecStart=/opt/gxp-copilot/.venv/bin/uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5
EnvironmentFile=/opt/gxp-copilot/.env

[Install]
WantedBy=multi-user.target
```

**Frontend Service (`/etc/systemd/system/gxp-frontend.service`)**:
```ini
[Unit]
Description=GxP IT AI Co-Pilot Frontend
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/opt/gxp-copilot/frontend
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=5
Environment=NODE_ENV=production
Environment=PORT=3000

[Install]
WantedBy=multi-user.target
```

**Enable and Start Services**:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now gxp-backend
sudo systemctl enable --now gxp-frontend
```

### 5. Configure NGINX Reverse Proxy (`/etc/nginx/sites-available/gxp`)
```nginx
server {
    listen 80;
    server_name your-server-ip-or-domain;

    # Frontend UI
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 60s;
    }

    # Swagger Documentation
    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
        proxy_set_header Host $host;
    }
    location /openapi.json {
        proxy_pass http://127.0.0.1:8000/openapi.json;
        proxy_set_header Host $host;
    }
}
```
Enable site and restart NGINX:
```bash
sudo ln -s /etc/nginx/sites-available/gxp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 6. Verification & Health Checks

After deployment, test the live system:

1. **Verify OpenRouter AI Model & Latency**:
   ```bash
   curl http://localhost:8000/api/v1/ai/health
   ```
   **Expected Response**:
   ```json
   {
     "provider": "OpenRouter",
     "model": "nvidia/nemotron-3.5-lightning:free",
     "status": "Healthy",
     "has_api_key": true,
     "base_url": "https://openrouter.ai/api/v1",
     "latency_ms": 806.6,
     "last_check": "2026-09-03T18:30:42Z"
   }
   ```

2. **Verify Cryptographic SHA-256 Audit Trail Integrity**:
   ```bash
   curl http://localhost:8000/api/v1/audit-log/verify
   ```
   **Expected Response**:
   ```json
   {
     "is_valid": true,
     "records_checked": 21,
     "message": "All audit trail records cryptographically verified. SHA-256 chain intact."
   }
   ```

3. **Run Automated Test Suite**:
   ```bash
   .venv/bin/pytest backend/tests/ -v
   ```
   **Expected Result**: `26 passed in ~5s (100% pass rate)`.
