# UniPCB Data Layout

The code expects all dataset paths to be relative to the repository root.

```text
data/benchmark/
  generated/
    generate_vqa_bilingual_test/
      all_vqa_data_bilingual_20260426_190307.json
  raw/
    PCBA/
    PCB-electric-resistance-Dataset_nodefect/
    FPIC/
    Dataset-PCB-CNN/
    AoI/
    DeepPCB/
    PCB-Defect-Detection-using-Image-Registration-master/
    VisA/
    solder-joint-dataset-main/
    pcb-component-detection/
  results/
```

The GitHub repository should contain code, documentation, and generated
annotation JSON files. The `raw/` image payload should be hosted through the
dataset URL, then unpacked into the same `data/benchmark/raw/` location.

Before upload or release, validate that every image path in the benchmark JSON
exists:

```bash
python scripts/dataset/validate_paths.py
```
