import argparse
import csv
import json
import os
import shutil
import urllib.request
import urllib.error
from pathlib import Path
from urllib.parse import urlencode

import cv2
import numpy as np
import requests
from PIL import Image
import imagehash

CLASS_NAMES = [
    "polymetallic_nodules",
    "cobalt_rich_crust",
    "hydrothermal_sulphide",
]

QUERIES = {
    "polymetallic_nodules": [
        "polymetallic nodules seafloor",
        "manganese nodules ROV",
        "Clarion Clipperton Zone nodules",
        "deep sea nodule field",
    ],
    "cobalt_rich_crust": [
        "cobalt-rich ferromanganese crust seamount",
        "cobalt crust rock specimen",
        "ferromanganese crust closeup",
        "seamount crust ROV",
    ],
    "hydrothermal_sulphide": [
        "hydrothermal vent black smoker",
        "massive sulphide deposit seafloor",
        "extinct sulphide mound",
        "seafloor massive sulphide specimen",
    ]
}

def get_existing_hashes(dataset_root: Path) -> set[str]:
    """Compute perceptual hashes for all existing images in the dataset to avoid duplicates."""
    print("Computing hashes for existing dataset to prevent duplicates...")
    hashes = set()
    for img_path in dataset_root.rglob("*"):
        if img_path.is_file() and img_path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
            try:
                img = Image.open(img_path)
                h = str(imagehash.average_hash(img))
                hashes.add(h)
            except Exception:
                pass
    return hashes

def fetch_bing_images(query: str, api_key: str, count: int) -> list[str]:
    print(f"Fetching '{query}' via Bing API...")
    url = "https://api.bing.microsoft.com/v7.0/images/search"
    headers = {"Ocp-Apim-Subscription-Key": api_key}
    urls = []
    for offset in range(0, count, 50):
        params = {"q": query, "count": min(50, count - offset), "offset": offset, "imageType": "Photo"}
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        for item in data.get("value", []):
            urls.append(item["contentUrl"])
    return urls

def fetch_serpapi_images(query: str, api_key: str, count: int) -> list[str]:
    print(f"Fetching '{query}' via SerpAPI...")
    url = "https://serpapi.com/search"
    urls = []
    
    params = {
        "engine": "google_images",
        "q": query,
        "api_key": api_key,
        "ijn": "0" 
    }
    
    page = 0
    while len(urls) < count:
        params["ijn"] = str(page)
        response = requests.get(url, params=params)
        if response.status_code != 200:
            print(f"SerpAPI Error: {response.text}")
            break
            
        data = response.json()
        images_results = data.get("images_results", [])
        if not images_results:
            break
            
        for item in images_results:
            urls.append(item["original"])
            if len(urls) >= count:
                break
        page += 1
    
    return urls

def is_blurry(image: np.ndarray, threshold: float = 100.0) -> bool:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    variance = cv2.Laplacian(gray, cv2.CV_64F).var()
    return variance < threshold

def is_uniform(image: np.ndarray, threshold: float = 10.0) -> bool:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    std_dev = np.std(gray)
    return std_dev < threshold

def main(target_class: str, target_count: int, dataset_root: Path):
    if target_class not in CLASS_NAMES:
        raise ValueError(f"Unknown class {target_class}. Must be one of {CLASS_NAMES}")

    bing_key = os.environ.get("BING_SEARCH_API_KEY")
    serpapi_key = os.environ.get("SERPAPI_KEY")

    if not bing_key and not serpapi_key:
        raise RuntimeError("No API key found. Set BING_SEARCH_API_KEY or SERPAPI_KEY environment variable.")

    raw_dir = dataset_root / "raw" / target_class
    pending_dir = dataset_root / "pending_review" / target_class
    raw_dir.mkdir(parents=True, exist_ok=True)
    pending_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = pending_dir / "fetch_manifest.csv"
    manifest_exists = manifest_path.exists()
    
    existing_hashes = get_existing_hashes(dataset_root)
    
    queries = QUERIES[target_class]
    urls_to_fetch = []
    
    count_per_query = max(10, target_count // len(queries) * 3)
    
    for query in queries:
        try:
            if bing_key:
                urls = fetch_bing_images(query, bing_key, count_per_query)
            else:
                urls = fetch_serpapi_images(query, serpapi_key, count_per_query)
            
            urls_to_fetch.extend([(query, u) for u in urls])
        except Exception as e:
            print(f"Failed to fetch for query '{query}': {e}")

    print(f"Discovered {len(urls_to_fetch)} candidate URLs. Beginning download and filter...")
    
    passed_count = 0
    filtered_out = 0
    
    with open(manifest_path, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not manifest_exists:
            writer.writerow(["image_name", "source_url", "query"])

        for i, (query, url) in enumerate(urls_to_fetch):
            if passed_count >= target_count:
                break
                
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as response:
                    img_array = np.asarray(bytearray(response.read()), dtype=np.uint8)
                    image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                
                if image is None:
                    filtered_out += 1
                    continue
                    
                h, w = image.shape[:2]
                if min(h, w) < 300:
                    filtered_out += 1
                    continue
                    
                if is_blurry(image):
                    filtered_out += 1
                    continue
                    
                if is_uniform(image):
                    filtered_out += 1
                    continue
                
                img_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
                img_hash = str(imagehash.average_hash(img_pil))
                
                if img_hash in existing_hashes:
                    filtered_out += 1
                    continue
                    
                existing_hashes.add(img_hash)
                
                img_name = f"fetched_{img_hash}.jpg"
                save_path = pending_dir / img_name
                cv2.imwrite(str(save_path), image)
                
                writer.writerow([img_name, url, query])
                passed_count += 1
                
                if passed_count % 5 == 0:
                    print(f"Progress: {passed_count}/{target_count} approved (Filtered out {filtered_out} junk images).")
                
            except Exception:
                filtered_out += 1
                continue

    print("\n--- FETCH SUMMARY ---")
    print(f"Target Class: {target_class}")
    print(f"Candidate URLs evaluated: {passed_count + filtered_out}")
    print(f"Images passed filters: {passed_count}")
    print(f"Images rejected (small, blurry, duplicates): {filtered_out}")
    print(f"Images ready for review in: {pending_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch and filter dataset images from search APIs.")
    parser.add_argument("--class-name", type=str, required=True, choices=CLASS_NAMES, help="Target class to fetch")
    parser.add_argument("--count", type=int, default=40, help="Number of valid images to accumulate")
    parser.add_argument("--dataset-root", type=Path, default=Path("dataset"), help="Dataset root directory")
    args = parser.parse_args()
    main(args.class_name, args.count, args.dataset_root)
