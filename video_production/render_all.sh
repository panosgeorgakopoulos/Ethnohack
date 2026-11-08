#!/bin/zsh
# Render every scene at 1080p30, one isolated media dir per scene (Manim's text cache is not concurrency-safe).
cd "$(dirname "$0")/manim"
M=../../.venv/bin/manim
render() { $M -qh --fps 30 --media_dir ../build/hq_$2 $1 $2 > ../build/hq_log_$2.txt 2>&1 && echo "ok $2" || echo "FAIL $2"; }
for s in E1Problem E2Method E3Example E4Selectivity E5Benchmark E6Ethno E7Close; do render explainer.py $s & done
for s in D1Launch D2Recommend D3Reveal D4Finalize D5Verdicts D6Benchmark; do render demo.py $s & done
wait
