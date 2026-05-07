# UniPCB Release and Hosting Notes

This document describes how to prepare the UniPCB code, dataset package, and
model weights for a repository release.

## GitHub Repository

Include:

- `README.md`
- `requirements.txt`
- `scripts/`
- `docs/`
- `data/benchmark/generated/`
- Croissant metadata file, after the final dataset URL is known

Exclude:

- `data/benchmark/raw/`
- `data/benchmark/results/`
- archives such as `*.zip`
- local credentials such as `.env`, API tokens, keys, and private config files
- paper source files containing identity or review metadata
- model checkpoints or large binary weights

## Dataset URL

The benchmark annotations are included in the GitHub repository, while raw
images are referenced through upstream public datasets listed in
`docs/data_sources.md`. If raw image redistribution is permitted and a separate
dataset package is hosted, the unpacked package should preserve this layout:

```text
unipcb_dataset/
  README.md
  LICENSE
  croissant.json
  data/
    benchmark/
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
```

If the hosted package is larger than the platform's single-file limit, split
`data/benchmark/raw/` by source dataset or into numbered archives. Keep the
unpacked paths identical to the layout above.

Validate the package before upload:

```bash
python scripts/dataset/validate_paths.py --root /path/to/unipcb_dataset
```

## Representative Sample

If a smaller inspection package is required, construct it with the same folder
layout and include a `sample_construction.md` file. The sample should be
stratified over source dataset, scenario category, language, and question type.
Document the sampling seed, target size, selection criteria, and whether images
are kept at full resolution.

## Model Weights

Host PCB-GPT weights in a separate model repository, for example on Hugging
Face. Use a project-scoped account or organization, and check that the model
card, profile, commit metadata, linked accounts, file names, and examples do not
contain identity information or absolute local paths.

Recommended model repository contents:

```text
PCB-GPT/
  README.md
  config.json
  generation_config.json
  tokenizer files
  model shard files
```

Use environment variables or command-line arguments for runtime configuration.
Do not commit credentials or endpoint-specific secrets.

## Croissant Metadata

Generate `croissant.json` after the final dataset URL is available. The metadata
should describe:

- dataset name, description, license, and version;
- dataset URL and file distributions;
- benchmark annotation fields;
- image path field and record structure;
- data provenance and construction pipeline;
- responsible AI fields required by the hosting venue.

Validate the Croissant file before submitting or linking it.

## Cleanup Checklist

- Run `python scripts/dataset/validate_paths.py` on the final data package.
- Search for local paths, credentials, user names, emails, and affiliation text.
- Confirm that `.gitignore` excludes raw data, results, archives, and secrets.
- Test dataset and model URLs from a clean browser session.
- Keep release links project-scoped and avoid personal accounts or personal
  storage URLs.
