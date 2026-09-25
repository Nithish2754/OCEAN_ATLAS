from __future__ import annotations

import argparse
from pathlib import Path

from .dataset import build_feature_store, save_dataset_manifest


def process_dataset(dataset_root: str | Path, output_dir: str | Path = "processed"):
    root = Path(dataset_root)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    feature_store = out_dir / "feature_store.npz"
    manifest = out_dir / "dataset_manifest.json"

    result = build_feature_store(root, feature_store)
    save_dataset_manifest(root, manifest)
    print(f"Saved {result['features'].shape[0]} feature rows to {feature_store}")
    print(f"Saved manifest to {manifest}")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process saved underwater image folders into a stored feature set.")
    parser.add_argument("--dataset-root", type=str, default="dataset", help="Folder containing the class directories")
    parser.add_argument("--output-dir", type=str, default="processed", help="Directory to store feature store and manifest")
    args = parser.parse_args()

    process_dataset(args.dataset_root, args.output_dir)
