#!/usr/bin/env bash
# Runs everything from the repo root (seed S = 2518).
set -e   # first: pip install -r requirements.txt
python setup/generate_data.py
python question_a/detect.py
python question_b/explain.py
python question_c/system_design.py
python question_c/capacity.py > question_c/capacity.md
python question_d/producer.py --speed 200      # fast replay just to fill the DB for measuring delay
python question_d/measure_delay.py
echo "Live demo:  python question_d/producer.py --speed 5   then   python -m streamlit run question_d/dashboard.py"
