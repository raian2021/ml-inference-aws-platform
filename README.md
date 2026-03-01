# Scalable ML Inference Platform on AWS (ECS Fargate + Terraform)

A cloud-native machine learning inference platform demonstrating production-grade engineering patterns:

- Model training pipeline (scikit-learn)
- FastAPI inference service
- Docker containerisation
- AWS ECS Fargate deployment
- Application Load Balancer (ALB)
- Infrastructure as Code (Terraform)
- CloudWatch logging
- Reproducible deploy → destroy lifecycle

---

## 🚀 Overview

This project implements an end-to-end ML inference system:

1. Train a binary classification model on synthetic financial data
2. Package the model as a containerised FastAPI service
3. Deploy to AWS ECS Fargate
4. Expose via an Application Load Balancer
5. Provision all infrastructure using Terraform
6. Tear down safely to avoid unnecessary cloud costs

The platform simulates a **credit risk / debt approval model**, returning probability scores and classification decisions.

---

## 🏗 Architecture

Client  
↓  
Application Load Balancer (HTTP)  
↓  
ECS Fargate Service (1 task)  
↓  
FastAPI Application  
↓  
Loaded scikit-learn Pipeline  
↓  
JSON Prediction Response  

Infrastructure is provisioned using Terraform.

---

## 🧠 Model Details

Model type: StandardScaler + LogisticRegression (scikit-learn pipeline)


Features:
- income
- age
- debt_ratio
- credit_score
- loan_amount
- employment_years

Outputs:
- probability
- binary label (threshold-based)

Metadata exposed via `/model-info`.

---

## 🧪 API Endpoints

### Health Check
GET /health


Response:
```json
{"status":"ok"}

GET /model-info

Returns:

model type

creation timestamp

training sample size

evaluation metrics

dependency versions

POST /predict

Example:

{
  "income": 45000,
  "age": 29,
  "debt_ratio": 0.32,
  "credit_score": 690,
  "loan_amount": 12000,
  "employment_years": 3
}

Response:

{
  "probability": 0.51,
  "label": 1,
  "model_version": "...",
  "threshold": 0.5
}

🐳 Docker

Build locally:

docker build -t ml-inference-api .

Run locally:

docker run -p 8000:8000 ml-inference-api
☁ AWS Deployment (Terraform)

Navigate to Terraform directory:

cd infra/terraform
terraform init
terraform apply -var="ecr_image=<ACCOUNT>.dkr.ecr.<REGION>.amazonaws.com/ml-inference-api:<TAG>"

Retrieve ALB URL:

terraform output -raw alb_url

Destroy infrastructure:

terraform destroy
🔐 Security & Cloud Design Decisions

Fargate (serverless containers — no EC2 management)

awsvpc network mode for task isolation

Security groups restrict ALB → task traffic

No hardcoded credentials

Terraform state excluded from Git

Infrastructure fully reproducible

📊 Observability

Container logs streamed to CloudWatch

Health checks via ALB target group

Model metadata endpoint for runtime introspection

💡 Engineering Concepts Demonstrated

Infrastructure as Code (Terraform)

Containerisation best practices

Multi-stage cloud architecture

Dependency version introspection

Model metadata surfacing

Cost-aware deploy/destroy lifecycle

Clean separation of training and inference

🔮 Potential Extensions

CI/CD via GitHub Actions

Blue/Green deployment strategy

Auto-scaling policies

HTTPS with ACM certificate

Model registry integration

Multi-model routing

LLM-based decision explanation layer

📌 Why This Project Matters

This project demonstrates not only ML modelling, but the operationalisation of ML systems:

Moving from notebook → container

Moving from local → cloud

Deploying using reproducible infrastructure

Managing cost and lifecycle responsibly

It represents a production-style ML engineering workflow.