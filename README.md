# ML Inference on AWS

**ECS Fargate · Application Load Balancer · Terraform · Docker · FastAPI**

A production-style machine learning inference platform deployed on AWS using ECS Fargate, Application Load Balancer, and Terraform.

This project includes:

- A containerised FastAPI inference service
- A scikit-learn model pipeline
- CloudWatch logging
- A fully reproducible deploy/destroy workflow

---

## What This Project Demonstrates

This repository is intentionally designed to demonstrate ML engineering and cloud operationalisation — not just modelling.

- Model training and packaging (scikit-learn pipeline + exported artefacts)
- Containerised inference API (FastAPI + Uvicorn + Docker)
- Infrastructure as Code (Terraform provisioning of AWS resources)
- Managed deployment (ECS Fargate, ALB routing, health checks)
- Observability (CloudWatch log group + streams)
- Cost-aware lifecycle (`terraform apply` and `terraform destroy`)

---

## High-Level Architecture

### Request Flow

```
Client
  → Application Load Balancer (HTTP :80)
    → Target Group (HTTP :8000, /health)
      → ECS Fargate Service (1 task)
        → FastAPI Inference App (Uvicorn)
          → scikit-learn Pipeline
            → JSON response
```

### Key Design Choices

- ALB handles public ingress and health checks
- ECS tasks run in `awsvpc` mode for network isolation
- Task traffic restricted via security groups (ALB → task only)
- Logs shipped to CloudWatch for debugging and runtime visibility

---

## Repository Structure

```
ml-inference-aws-platform/
├── app/                    # FastAPI inference service
├── model/                  # training code + exported artefacts
│   └── artifacts/          # model.joblib, metadata.json
├── infra/
│   └── terraform/          # AWS ECS + ALB + VPC Infrastructure as Code
├── tests/                  # unit/integration tests
├── Dockerfile              # container build
├── requirements.txt        # Python dependencies
└── README.md
```

---

## Model Details

### Model Type

StandardScaler + LogisticRegression (scikit-learn pipeline)

### Features

- `income`
- `age`
- `debt_ratio`
- `credit_score`
- `loan_amount`
- `employment_years`

### Outputs

- `probability` (float)
- `label` (int, threshold-based)
- `model_version` (timestamp string)
- `threshold` (float)

The deployed service exposes runtime metadata (including dependency versions and evaluation metrics) via `/model-info`.

---

## API Endpoints

### Health Check

**Request:**

```http
GET /health
```

**Response:**

```json
{"status": "ok"}
```

### Model Metadata

**Request:**

```http
GET /model-info
```

**Response (example):**

```json
{
  "model_type": "sklearn.pipeline(StandardScaler + LogisticRegression)",
  "created_utc": "2026-03-01T16:39:42.590227+00:00",
  "seed": 42,
  "n_samples": 15000,
  "threshold": 0.5,
  "features": ["income", "age", "debt_ratio", "credit_score", "loan_amount", "employment_years"],
  "metrics": {"roc_auc": 0.6611, "accuracy": 0.615},
  "deps": {"sklearn": "1.8.0", "numpy": "2.4.2", "pandas": "3.0.1"}
}
```

### Predict

**Request:**

```http
POST /predict
Content-Type: application/json
```

**Body:**

```json
{
  "income": 45000,
  "age": 29,
  "debt_ratio": 0.32,
  "credit_score": 690,
  "loan_amount": 12000,
  "employment_years": 3
}
```

**Response (example):**

```json
{
  "probability": 0.5147535266593802,
  "label": 1,
  "model_version": "2026-03-01T16:39:42.590227+00:00",
  "threshold": 0.5
}
```

---

## Local Development

### 1. Activate environment

```bash
conda activate inference_platform
```

### 2. Run the API locally

From the repository root:

```bash
python -m app.main
```

### 3. Test locally

```bash
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8000/model-info
```

---

## Docker

### Build locally

```bash
docker build -t ml-inference-api .
```

### Run locally

```bash
docker run -p 8000:8000 ml-inference-api
```

### Test container

```bash
curl -s http://127.0.0.1:8000/health
```

---

## AWS Deployment (ECS Fargate + ALB) Using Terraform

> ⚠️ **AWS resources can incur cost. Run `terraform destroy` when finished.**

### Prerequisites

- AWS CLI installed and configured (`aws configure`)
- Docker installed
- Terraform installed
- ECR repository created

### 1. Build and Push Image to ECR

Authenticate Docker to ECR:

```bash
aws ecr get-login-password --region eu-west-2 \
  | docker login --username AWS --password-stdin .dkr.ecr.eu-west-2.amazonaws.com
```

Build and push (Linux amd64 required for ECS):

```bash
docker buildx build \
  --platform linux/amd64 \
  -t .dkr.ecr.eu-west-2.amazonaws.com/ml-inference-api:latest \
  --push .
```

### 2. Deploy Infrastructure

```bash
cd infra/terraform
terraform init
```

Apply:

```bash
terraform apply \
  -var="ecr_image=.dkr.ecr.eu-west-2.amazonaws.com/ml-inference-api:latest"
```

Retrieve ALB URL:

```bash
terraform output -raw alb_url
```

### 3. Test Deployed Service

```bash
ALB="$(terraform output -raw alb_url)"

curl -s "$ALB/health"
curl -s "$ALB/model-info"

curl -s -X POST "$ALB/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "income": 45000,
    "age": 29,
    "debt_ratio": 0.32,
    "credit_score": 690,
    "loan_amount": 12000,
    "employment_years": 3
  }'
```

### 4. View Logs (CloudWatch)

List log streams:

```bash
aws logs describe-log-streams \
  --log-group-name /ecs/ml-inference \
  --region eu-west-2 \
  --order-by LastEventTime \
  --descending \
  --max-items 10
```

Tail logs:

```bash
aws logs get-log-events \
  --log-group-name /ecs/ml-inference \
  --log-stream-name "" \
  --region eu-west-2 \
  --limit 50
```

### 5. Destroy Infrastructure

```bash
terraform destroy
```

This removes the VPC, ALB, ECS service, task definition, IAM role, and log group.

---

## Infrastructure Design Notes

- ALB exposes HTTP :80 publicly and forwards to :8000
- Target group health check hits `/health`
- Task security group allows inbound :8000 only from ALB security group
- `awsvpc` mode gives each task its own ENI
- CloudWatch logs provide runtime inspection
- No secrets committed (Terraform state excluded)

---

## Common Issues and Fixes

### `Manifest does not contain descriptor matching platform 'linux/amd64'`

Occurs when image is built for arm64 (Apple Silicon).

**Fix:**

```bash
docker buildx build --platform linux/amd64 -t :latest --push .
```

Force new deployment:

```bash
aws ecs update-service \
  --cluster ml-inference-cluster \
  --service ml-inference-svc \
  --force-new-deployment \
  --region eu-west-2
```

### ALB Returns 503

Targets are not healthy yet. Check:

- ECS service events
- Task status
- CloudWatch logs
- Target group health

---

## Next Steps

- CI/CD pipeline with GitHub Actions
- HTTPS with ACM
- Auto-scaling policies
- Blue/Green or Canary deployments
- Structured logging and tracing
- LLM-based decision explanation layer