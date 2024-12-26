#!/bin/bash

# Set exit on error
set -e

# If there is no CI env variable, this is local execution
if [[ -z "${CI}" ]]; then
  echo "This is local execution"
else
  echo "This is CI/CD execution"
fi
