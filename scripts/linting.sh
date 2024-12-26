#!/bin/bash

# Set exit on error
set -e
CODE_QUALITY=3
MAX_LENGTH=120

# If there is no CI env variable, this is local execution
if [[ -z "${CI}" ]]; then
  echo "This is local execution"
  source ./.venv/bin/activate
  black .
  isort . --profile black --filter-files
  pylint ./src ./tests --fail-under="${CODE_QUALITY}" --disable=W1203 --max-line-length=${MAX_LENGTH}
  yamllint -d "{extends: default, rules: {line-length: {max: ${MAX_LENGTH}}, truthy: false}}" ./.codecatalyst ./infra
else
  echo "This is CI/CD execution"
  black . --check
  isort . --profile black --filter-files --check-only
  pylint ./src ./tests --fail-under="${CODE_QUALITY}" --disable=W1203 --max-line-length=${MAX_LENGTH}
  yamllint -d "{extends: default, rules: {line-length: {max: ${MAX_LENGTH}}, truthy: false}}" ./.codecatalyst ./infra
fi
