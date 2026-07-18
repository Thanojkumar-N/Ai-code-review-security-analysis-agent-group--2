# Production Deployment Guide

This document details the configuration requirements and provisioning steps to deploy the AI Code Review & Security Analysis Agent workspace to AWS, Render, or Railway.

---

## 🔐 Environment Variables Configuration

Ensure the following variables are configured in the cloud settings dashboard:

| Variable Name | Description | Suggested Value |
| --- | --- | --- |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/dbname` |
| `JWT_SECRET` | Secure key to sign user cookies and tokens | Generate using `openssl rand -hex 32` |
| `JWT_ALGORITHM` | Hash algorithm for JWT | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access Token duration limit | `30` |
| `ENVIRONMENT` | Deployment stage | `production` |

---

## ☁️ AWS Provisioning (ECS & App Runner)

### AWS App Runner (Fast API Backend)
1. Navigate to the **AWS App Runner** dashboard.
2. Select **Source Code Repository** or **Container Registry** (ECR).
3. Connect your repository and select the root directory branch.
4. Set runtime configuration:
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.app.main:app --host 0.0.0.0 --port 8080`
5. Configure environment variables in the App Runner console.
6. Click **Create & Deploy**.

### AWS ECS / Fargate (Containerized Stack)
We configure the ECS service using the workspace [docker-compose.yml](file:///c:/Users/thano/Downloads/ai-code-review-security-agent/docker-compose.yml) task definition mappings.
1. Push images to **Amazon ECR**.
2. Define a task definition containing container specifications for `postgres`, `backend`, `frontend`, and `nginx`.
3. Launch Fargate services within a secure VPC mapping traffic through an Application Load Balancer.

---

## 🚀 Render Provisioning
Deploy the complete multi-service stack using Render blueprints:
1. Connect your repository to **Render**.
2. Click **New** -> **Blueprint Route**.
3. Select the repository. Render will automatically parse [render.yaml](file:///c:/Users/thano/Downloads/ai-code-review-security-agent/render.yaml) and spin up:
   - PostgreSQL Database instance
   - FastAPI Backend web service
   - React static frontend web app
4. Click **Apply**.

---

## 🚃 Railway Provisioning
1. Open the **Railway** console.
2. Click **New Project** -> **Deploy from GitHub**.
3. Connect your repository branch.
4. Railway parses [railway.json](file:///c:/Users/thano/Downloads/ai-code-review-security-agent/railway.json) to spin up the Nixpacks python compilation build and start the Uvicorn web daemon.
5. Add a **PostgreSQL plugin** container and map the connection URL to the `DATABASE_URL` environment variables.
