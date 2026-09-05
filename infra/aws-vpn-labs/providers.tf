provider "aws" {
  region = var.aws_region

  default_tags {
    tags = merge(
      var.extra_tags,
      {
        Project   = var.project_name
        ManagedBy = "terraform"
        Purpose   = "authorized-software-security-training"
      }
    )
  }
}

data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}
data "aws_partition" "current" {}
