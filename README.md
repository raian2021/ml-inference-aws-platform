# ML Inference on AWS (ECS Fargate + ALB + Terraform)

A production-style machine learning inference platform deployed on AWS using **ECS Fargate**, **Application Load Balancer**, and **Terraform**.  
Includes a containerised **FastAPI** inference service, a scikit-learn model pipeline, CloudWatch logging, and an end-to-end deploy/destroy workflow.

---

## What this project demonstrates

This repo is intentionally designed to show **ML engineering + cloud operationalisation**, not just modelling.

- **Model training and packaging** (scikit-learn pipeline + exported artefacts)
- **Containerised inference API** (FastAPI + Uvicorn + Docker)
- **Infrastructure as Code** (Terraform provisioning of AWS resources)
- **Managed deployment** (ECS Fargate, ALB routing, health checks)
- **Observability** (CloudWatch log group + streams)
- **Cost-aware lifecycle** (repeatable `terraform apply` and `terraform destroy`)

---

## High-level architecture

Request flow:
Client
-> Application Load Balancer (HTTP :80)
-> Target Group (HTTP :8000, /health)
-> ECS Fargate Service (1 task)
-> FastAPI Inference App (Uvicorn)
-> scikit-learn Pipeline
-> JSON response


Key design choices:

- ALB handles **public ingress** and health checks.
- ECS tasks run in **awsvpc mode** for network isolation.
- Task traffic is restricted via **security groups** (ALB -> task only).
- Logs are shipped to **CloudWatch** for debugging and runtime visibility.

---

## Repository structure
ml-inference-aws-platform/
├─ app/ # FastAPI service (inference API)
├─ model/ # training + artefacts (joblib + metadata)
│ └─ artifacts/ # model.joblib, metadata.json, etc.
├─ infra/
│ └─ terraform/ # AWS ECS + ALB + VPC IaC
├─ tests/ # unit/integration tests
├─ Dockerfile # container build for inference service
├─ requirements.txt # Python dependencies
└─ README.md



---

## Model details

### Model type
- `StandardScaler + LogisticRegression` (scikit-learn pipeline)

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
- `model_version` (timestamp/version string)
- `threshold` (float)

The deployed service exposes runtime metadata (including dependency versions and evaluation metrics) via `/model-info`.

---

## API endpoints

### Health check

**Request**
```http
GET /health

Response

{"status":"ok"}


Model metadata

Request

GET /model-info

Response (example)

{
  "model_type": "sklearn.pipeline(StandardScaler + LogisticRegression)",
  "created_utc": "2026-03-01T16:39:42.590227+00:00",
  "seed": 42,
  "n_samples": 15000,
  "threshold": 0.5,
  "features": ["income","age","debt_ratio","credit_score","loan_amount","employment_years"],
  "metrics": {"roc_auc": 0.6611, "accuracy": 0.615},
  "deps": {"sklearn":"1.8.0","numpy":"2.4.2","pandas":"3.0.1"}
}
Predict

Request

POST /predict
Content-Type: application/json

Body

{
  "income": 45000,
  "age": 29,
  "debt_ratio": 0.32,
  "credit_score": 690,
  "loan_amount": 12000,
  "employment_years": 3
}

Response (example)

{
  "probability": 0.5147535266593802,
  "label": 1,
  "model_version": "2026-03-01T16:39:42.590227+00:00",
  "threshold": 0.5
}








Local development
1) Activate environment
conda activate inference_platform
2) Run the API locally

From the repo root:

python -m app.main

Test:

curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8000/model-info
Docker
Build locally
docker build -t ml-inference-api .
Run locally
docker run -p 8000:8000 ml-inference-api

Test:

curl -s http://127.0.0.1:8000/health
AWS deployment (ECS Fargate + ALB) using Terraform

Note: AWS resources can incur cost. Use terraform destroy when finished.

Prerequisites

AWS CLI installed and configured (aws configure)

Docker installed

Terraform installed

ECR repository created (or created manually via AWS CLI)

1) Build and push image to ECR

Authenticate Docker to ECR (region example: eu-west-2):

aws ecr get-login-password --region eu-west-2 \
  | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.eu-west-2.amazonaws.com

Build and push (Linux amd64 for ECS):

docker buildx create --use --name multiarchbuilder 2>/dev/null || true

docker buildx build \
  --platform linux/amd64 \
  -t <ACCOUNT_ID>.dkr.ecr.eu-west-2.amazonaws.com/ml-inference-api:latest \
  --push .
2) Deploy infrastructure
cd infra/terraform
terraform init

Apply (image passed as a variable):

terraform apply \
  -var="ecr_image=<ACCOUNT_ID>.dkr.ecr.eu-west-2.amazonaws.com/ml-inference-api:latest"

Retrieve ALB URL:

terraform output -raw alb_url
3) Test the deployed service
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
4) View logs (CloudWatch)

List log streams:

aws logs describe-log-streams \
  --log-group-name /ecs/ml-inference \
  --region eu-west-2 \
  --order-by LastEventTime \
  --descending \
  --max-items 10

Tail logs for a specific stream:

aws logs get-log-events \
  --log-group-name /ecs/ml-inference \
  --log-stream-name "<STREAM_NAME>" \
  --region eu-west-2 \
  --limit 50
5) Destroy infrastructure (stop charges)
terraform destroy

This removes the VPC, ALB, ECS service/task definition, IAM role, and log group created by Terraform.

Infrastructure design notes

ALB exposes HTTP :80 publicly and forwards to target group on :8000

Target group health check hits /health

Task security group only allows inbound :8000 from the ALB security group

awsvpc mode gives each task its own ENI (isolation and clear security boundaries)

CloudWatch logs provide runtime inspection without shell access into containers

No secrets committed (Terraform state excluded; credentials are via AWS CLI profile)

Common issues and fixes
“Manifest does not contain descriptor matching platform 'linux/amd64'”

You built/pushed an image for the wrong architecture (often arm64 on Apple Silicon).

Fix: rebuild and push using:

docker buildx build --platform linux/amd64 -t <ECR_URI>:latest --push .

Then force a new deployment:

aws ecs update-service \
  --cluster ml-inference-cluster \
  --service ml-inference-svc \
  --force-new-deployment \
  --region eu-west-2
ALB returns 503 Service Temporarily Unavailable

Usually means targets are not healthy yet (task still starting or failing).

Check:

ECS service events

Task status

CloudWatch logs

Target group health

Next steps (extensions)

These are the most natural production upgrades:

CI/CD pipeline (GitHub Actions) to build/push image + terraform apply

HTTPS termination with ACM + redirect HTTP -> HTTPS

Auto-scaling based on CPU / request count

Blue/green or canary deployments

Add request tracing + structured logs

Add an LLM “explanation layer” for model decisions (optional, gated by API key)