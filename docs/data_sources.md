# UniPCB Data Sources

UniPCB uses repository-relative annotation paths and does not require raw image
files to be stored in the code repository. The benchmark annotations are
included in `data/benchmark/generated/`; raw image files can be obtained from the
upstream public sources listed below and organized under `data/benchmark/raw/`.

This source manifest is provided to support review-time inspection and
reproducibility while respecting source-level licenses and access terms. A small
format-preview subset is included under `examples/`.

## Benchmark Source Manifest

| UniPCB folder | Upstream source | URL | Terms | Used samples | Used image refs |
| --- | --- | --- | --- | ---: | ---: |
| `PCBA` | PCBA-DET | https://github.com/ismh16/PCBA-Dataset | Research use | 873 | 873 |
| `PCB-electric-resistance-Dataset_nodefect` | PCB Resistor Defect Dataset | https://github.com/leiruoshan/PCB-Resistor-Defect-Dataset | Research use | 960 | 960 |
| `FPIC` | FICS PCB Image Collection / FPIC | https://physicaldb.ece.ufl.edu/index.php/fics-pcb-image-collection-fpic/ | Registered access | 943 | 943 |
| `Dataset-PCB-CNN` | Dataset-PCB | https://github.com/asrf001/DatasetPCB/tree/master | Research use | 325 | 325 |
| `AoI` | PCB-AoI | https://www.kaggle.com/datasets/kubeedgeianvs/pcb-aoi/data | Apache-2.0 | 630 | 630 |
| `DeepPCB` | DeepPCB | https://github.com/tangsanli5201/DeepPCB | Research use | 398 | 796 |
| `PCB-Defect-Detection-using-Image-Registration-master` | PCB Defect Detection using Image Registration | https://github.com/vihangp/PCB-Defect-Detection-using-Image-Registration/tree/master | Research use | 28 | 56 |
| `VisA` | VisA / Spot-the-Difference industrial anomaly data | https://github.com/amazon-science/spot-diff | CC BY 4.0 | 398 | 796 |
| `solder-joint-dataset-main` | Solder Joint Dataset | https://github.com/furkanulger/solder-joint-dataset?tab=readme-ov-file | Research use | 381 | 381 |
| `pcb-component-detection` | PCB Component Detection | https://datasetninja.com/pcb-component-detection | CC0 1.0 | 800 | 800 |

## Expected Local Layout

After obtaining source data, organize or preprocess the image payload so that
the annotation paths resolve under the following layout:

```text
data/benchmark/raw/
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
```

Validate local image references with:

```bash
python scripts/dataset/validate_paths.py
```

The current benchmark annotation package expects:

```text
records=5736
image_refs=6560
unique_image_refs=6560
missing=0
```

## Review-Time Access Notes

- `examples/` contains a small self-contained preview subset with copied images
  and rewritten paths.
- `data/benchmark/generated/` contains the full VQA annotation JSON.
- The full raw image payload is not committed to GitHub because source datasets
  have different redistribution terms.
- For sources requiring registration or platform login, reviewers should follow
  the upstream access instructions.
- Source licenses and access terms should be checked before redistributing raw
  images outside the original platforms.
