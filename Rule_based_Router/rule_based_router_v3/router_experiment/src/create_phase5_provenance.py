"""Create Phase 5 split/leakage and Phase 4 manifest artifacts."""

import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rows(path):
    with open(path, encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def normalize(question):
    return re.sub(r"[^a-z0-9 ]+", " ", question.lower()).split()


def near_duplicate(left, right):
    a, b = set(normalize(left)), set(normalize(right))
    return bool(a and b) and len(a & b) / len(a | b) >= 0.8


def git_commit():
    return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()


def main(data_dir, output_dir, experiment_root):
    os.makedirs(output_dir, exist_ok=True)
    dev = Path(experiment_root) / "data" / "test_router.jsonl"
    validation = Path(data_dir) / "validation.jsonl"
    holdout = Path(data_dir) / "holdout.jsonl"
    split_rows = {"development": rows(dev), "validation": rows(validation), "holdout": rows(holdout)}
    duplicate_pairs = []
    near_duplicate_pairs = []
    for left_name, left_rows in split_rows.items():
        for right_name, right_rows in split_rows.items():
            if left_name >= right_name:
                continue
            for left in left_rows:
                for right in right_rows:
                    if left["question"].strip().lower() == right["question"].strip().lower():
                        duplicate_pairs.append([left_name, left["id"], right_name, right["id"]])
                    elif near_duplicate(left["question"], right["question"]):
                        near_duplicate_pairs.append([left_name, left["id"], right_name, right["id"]])
    leakage = {
        "development": {"path": str(dev), "sha256": sha256(dev), "samples": len(split_rows["development"]), "provenance": "historical Rule V3 development/regression set; used in Phases 1-4"},
        "validation": {"path": str(validation), "sha256": sha256(validation), "samples": len(split_rows["validation"]), "provenance": "new generated split authored before Phase 5 threshold search"},
        "holdout": {"path": str(holdout), "sha256": sha256(holdout), "samples": len(split_rows["holdout"]), "provenance": "new generated split frozen before Phase 5 tuning; not read by search"},
        "exact_duplicate_pairs": duplicate_pairs,
        "near_duplicate_pairs": near_duplicate_pairs,
        "duplicate_count": len(duplicate_pairs),
        "near_duplicate_count": len(near_duplicate_pairs),
    }
    with open(Path(output_dir) / "v3_phase_5_duplicate_leakage_report.json", "w", encoding="utf-8") as file:
        json.dump(leakage, file, ensure_ascii=False, indent=2)

    phase4_output = Path(experiment_root) / "outputs" / "phase_4"
    files = {}
    for path in sorted(phase4_output.iterdir()):
        if path.is_file():
            files[str(path.relative_to(experiment_root)).replace("\\", "/")] = sha256(path)
    manifest = {
        "phase": "phase_5",
        "baseline_phase": "phase_4",
        "git_commit_sha": git_commit(),
        "phase4_files": files,
        "note": "Manifest only; Phase 4 artifacts are referenced by path and SHA256, not copied recursively.",
    }
    with open(Path(output_dir) / "v3_phase_5_reproducibility_manifest.json", "w", encoding="utf-8") as file:
        json.dump(manifest, file, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--experiment-root", required=True)
    args = parser.parse_args()
    main(args.data_dir, args.output_dir, args.experiment_root)
