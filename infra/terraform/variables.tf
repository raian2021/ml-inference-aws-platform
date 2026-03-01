variable "aws_region" {
  type    = string
  default = "eu-west-2"
}

variable "ecr_image" {
  type        = string
  description = "ECR image URI incl tag, e.g. 123.dkr.ecr.eu-west-2.amazonaws.com/ml-inference-api:latest"
}
