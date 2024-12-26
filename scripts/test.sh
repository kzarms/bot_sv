#!/bin/bash

# Set exit on error
set -e
COVERAGE=30

# If there is no CI env variable, this is local execution
if [[ -z "${CI}" ]]; then
  echo "This is local execution"
  source ./.venv/bin/activate
  pytest -sv --cov=./src --cov-fail-under="${COVERAGE}" --cov-report=term-missing
  deactivate
else
  echo "This is CI/CD execution"
  export AWS_ACCOUNT_ID="111111111111"
  pytest -sv --cov=./src --cov-fail-under="${COVERAGE}" --cov-report=xml:test_unit_coverage.xml --junitxml=test_unit_results.xml
fi
