#!/bin/bash

# If there is no CI env variable, this is local execution
if [[ -z "${CI}" ]]; then
  echo "This is local execution"
  python3.11 -m venv .venv
  source ./.venv/bin/activate
  pip install -r requirements.txt
else
  echo "This is CI/CD execution"
  python3 --version
  pip3 install -r requirements.txt
fi
