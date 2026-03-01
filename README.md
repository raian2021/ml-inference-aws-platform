Scalable ML Inference Platform on AWS

ECS Fargate • Application Load Balancer • Terraform • Docker • FastAPI

Overview

This project implements an end-to-end, production-style machine learning inference platform deployed to AWS using Infrastructure as Code.

The system demonstrates the complete operationalisation lifecycle of an ML model:

Model training (scikit-learn)

Containerised inference service (FastAPI + Docker)

Cloud deployment (AWS ECS Fargate)

Traffic routing (Application Load Balancer)

Infrastructure provisioning (Terraform)

Observability (CloudWatch logs)

Cost-aware deploy and destroy lifecycle

The platform simulates a credit risk / debt approval classifier and exposes prediction endpoints over HTTP.

Architecture

Client
→ Application Load Balancer (HTTP)
→ ECS Fargate Service (1 task)
→ FastAPI Inference Application
→ scikit-learn Pipeline
→ JSON Response

All infrastructure is provisioned and destroyed using Terraform.

Model Design

Model type:

StandardScaler + LogisticRegression (scikit-learn pipeline)

Features:

income

age

debt_ratio

credit_score

loan_amount

employment_years

Outputs:

probability (float)

binary classification label (threshold-based decision)

Model metadata (including dependency versions and evaluation metrics) is exposed via the /model-info endpoint.

API Specification
Health Check

GET /health

Response:

{
  "status": "ok"
}
Model Metadata

GET /model-info

Returns:

model type

creation timestamp

training sample size

evaluation metrics

dependency versions

Prediction Endpoint

POST /predict

Example request:

{
  "income": 45000,
  "age": 29,
  "debt_ratio": 0.32,
  "credit_score": 690,
  "loan_amount": 12000,
  "employment_years": 3
}

Example response:

{
  "probability": 0.51,
  "label": 1,
  "model_version": "2026-03-01T16:39:42Z",
  "threshold": 0.5
}
Local Development

Activate environment:

conda activate inference_platform

Run API locally:

python -m app.main

Service available at:

http://localhost:8000
Docker

Build container image:

docker build -t ml-inference-api .

Run container:

docker run -p 8000:8000 ml-inference-api
AWS Deployment

Navigate to Terraform directory:

cd infra/terraform
terraform init

Deploy infrastructure:

terraform apply -var="ecr_image=<ACCOUNT>.dkr.ecr.<REGION>.amazonaws.com/ml-inference-api:<TAG>"

Retrieve load balancer URL:

terraform output -raw alb_url

Destroy infrastructure (recommended after testing to avoid charges):

terraform destroy
Infrastructure Design Decisions

ECS Fargate (serverless containers, no EC2 management)

awsvpc network mode for task isolation

Application Load Balancer for external routing

Security groups restricting ALB-to-task communication

CloudWatch log streaming for container output

No hardcoded credentials

Terraform state excluded from version control

Fully reproducible infrastructure lifecycle

Observability

Container logs streamed to CloudWatch

ALB health checks targeting /health

Runtime model metadata endpoint

Deterministic model versioning via timestamp

Engineering Concepts Demonstrated

Infrastructure as Code (Terraform)

Containerisation best practices

Cloud-native service architecture

Separation of training and inference

API contract definition

Dependency introspection

Cost-aware infrastructure lifecycle management

Production-style ML system operationalisation

Potential Extensions

CI/CD via GitHub Actions

Blue/Green or Canary deployment strategy

Auto-scaling policies

HTTPS with ACM certificate

Model registry integration

Multi-model routing

LLM-based decision explanation layer

Metrics collection via Prometheus / CloudWatch metrics

Purpose

This project demonstrates not only ML modelling capability, but the ability to operationalise ML systems in a cloud-native environment using industry-standard tooling and infrastructure practices.

It represents a production-oriented ML engineering workflow rather than a notebook-only implementation.