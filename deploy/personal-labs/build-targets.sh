#!/usr/bin/env bash
# A minimal context works with both legacy Docker builders and BuildKit.
set -euo pipefail
cd "$(dirname "$0")/../.."
task_context=$(mktemp -d)
trap 'rm -rf "$task_context"' EXIT
cp deploy/semester-labs/target.Dockerfile "$task_context/Dockerfile"
for source_dir in labs/week10-api-security labs/week14-ai-llm-security labs/week15-devsecops-pipeline; do
  mkdir -p "$task_context/$source_dir"
done
for source in labs/week10-api-security/{vulnerable_api,solution_api}.py \
              labs/week14-ai-llm-security/{vulnerable_chatbot,guarded_chatbot}.py \
              labs/week15-devsecops-pipeline/{insecure_service,secure_service}.py; do
  cp "$source" "$task_context/$source"
done
for target in api-vulnerable api-defended ai-vulnerable ai-defended ops-vulnerable ops-defended; do
  case "$target" in
    api-*) source_dir=labs/week10-api-security;;
    ai-*) source_dir=labs/week14-ai-llm-security;;
    ops-*) source_dir=labs/week15-devsecops-pipeline;;
  esac
  docker build --network=host --build-arg "LAB_DIR=$source_dir" \
    -t "software-security-semester-$target:latest" "$task_context"
done
