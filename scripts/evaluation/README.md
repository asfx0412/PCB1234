# UniPCB Evaluation

This folder contains the cleaned evaluation pipeline. It does not modify or move
the original `ff` files.

## 1. Run Inference

Use an OpenAI-compatible API such as vLLM:

```bash
python scripts/evaluation/run_inference.py \
  --input data/benchmark/generated/generate_vqa_bilingual_test/all_vqa_data_bilingual_20260426_190307.json \
  --output data/benchmark/results/raw_predictions/model_predictions.json \
  --api_base http://localhost:8000/v1 \
  --model PCB-GPT
```

The output is the original benchmark JSON with `model_response` added to every
conversation item.

## 2. Evaluate Predictions

```bash
python scripts/evaluation/evaluate.py \
  --input data/benchmark/results/raw_predictions/model_predictions.json \
  --output data/benchmark/results/evaluated/model_evaluation.json
```

Metrics:

- Multiple choice: exact A/B/C/D accuracy.
- Coordinates: class-aware IoU matching with configurable threshold.
- Open text: lightweight token F1 and character similarity.

LLM-as-judge and heavier semantic metrics can be added as optional extensions.

## 3. Optional LLM-As-Judge

For open-ended answers:

```bash
python scripts/evaluation/llm_judge.py \
  --input data/benchmark/results/raw_predictions/model_predictions.json \
  --output data/benchmark/results/evaluated/model_llm_judge.json \
  --api_base http://localhost:8000/v1 \
  --model PCB-GPT
```

Use `--sample_fraction` or `--max_items` for cheaper spot checks.
