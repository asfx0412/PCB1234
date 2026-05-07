# UniPCB VQA Manual Review

Start the local review UI:

```bash
python scripts/manual_review/review_server.py --host 127.0.0.1 --port 8008
```

Then open:

```text
http://127.0.0.1:8008
```

By default the server reads:

```text
data/benchmark/generated/generate_vqa_bilingual_test/all_vqa_data_bilingual_20260426_190307.json
```

Review decisions are saved separately to:

```text
data/benchmark/generated/generate_vqa_bilingual_test/manual_review_20260426_190307.json
```

Use `--data-file` and `--review-file` to review another generated file or write to a different output.

For multiple reviewers, use a different reviewer name in the page header, or start separate ports:

```bash
python scripts/manual_review/review_server.py --host 127.0.0.1 --port 8008 --reviewer reviewer1
python scripts/manual_review/review_server.py --host 127.0.0.1 --port 8009 --reviewer reviewer2
```

The default reviewer writes to the base review file. Other reviewers write sibling files such as:

```text
manual_review_20260426_190307_reviewer2.json
```
