#!/bin/bash
python3 -m pytest tests/ --tb=no -q --maxfail=100 2>&1 | tee test_output.txt
