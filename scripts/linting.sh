#!/bin/bash

# Set exit on error
set -e
CODE_QUALITY=8
MAX_LENGTH=120

# If there is no CI env variable, this is local execution
if [[ -z "${CI}" ]]; then
  echo "This is local execution"
  source ./.venv/bin/activate
  black .
  isort . --profile black --filter-files
  pylint ./src --fail-under="${CODE_QUALITY}" --disable="C0301,W1203"
  yamllint -d "{extends: default, rules: {line-length: {max: ${MAX_LENGTH}}, truthy: false}}" ./.github ./infra
else
  echo "This is CI/CD execution"
  black . --check
  isort . --profile black --filter-files --check-only
  pylint ./src --fail-under="${CODE_QUALITY}" --disable="C0301,W1203"
  yamllint -d "{extends: default, rules: {line-length: {max: ${MAX_LENGTH}}, truthy: false}}" ./.github ./infra
fi
