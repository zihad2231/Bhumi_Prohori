"""
EasyLand AI CV engine.

Important:
- This module detects candidate boundaries in an image using OpenCV.
- Pixel coordinates are NOT GPS coordinates.
- It does not determine real Dag numbers, legal boundaries, ownership, or verification status.
- GeoJSON is deliberately empty unless reliable georeferencing is supplied by a future, separate workflow.
"""

from pathlib import Path
import json

import cv2
import numpy as np


def create_dummy_mouza_map(filepath="processed_data/sample_mouza.png"):
    """
    Create a clearly synthetic image for local testing only.
    Never use this generated image as a real cadastral/mouza map.
    """
    output_path = Path(filepath)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    img = np.full((600, 600, 3), 255, dtype=np.uint8)
    plots = [
        [(50, 50), (280, 50), (270, 260), (50, 250)],
        [(290, 50), (550, 60), (540, 270), (280, 260)],
        [(50, 270), (270, 280), (260, 540), (60, 530)],
        [(280, 280), (540, 290), (530, 550), (275, 540)],
    ]

    for index, polygon in enumerate(plots, start=1):
        points = np.array(polygon, dtype=np.int32).reshape((-1, 1, 2))
        cv2.polylines(img, [points], isClosed=True, color=(0, 0, 0), thickness=3)
        cv2.putText(
            img, f"SAMPLE {index}",
            (polygon[0][0] + 8, polygon[0][1] + 24),
            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (100, 100, 100), 1, cv2.LINE_AA
        )

    if not cv2.imwrite(str(output_path), img):
        raise OSError(f"Could not write sample image: {output_path}")

    return str(output_path)


def process_mouza_map(image_path: str, output_dir="processed_data"):
    """
    Detect candidate contours in a supplied image.

    The result stores image pixel polygons in candidate_boundaries.json.
    It does NOT convert pixels into GPS and returns an empty GeoJSON overlay,
    because georeferencing/cadastral control points are not available.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError("Input image not found or unreadable.")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    kernel = np.ones((3, 3), dtype=np.uint8)
    closed_edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(
        closed_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    preview = image.copy()
    candidates = []

    for contour in contours:
        area = float(cv2.contourArea(contour))
        if area < 5000:
            continue

        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        if len(approx) < 3:
            continue

        pixel_points = [[int(point[0][0]), int(point[0][1])] for point in approx]
        cv2.drawContours(preview, [approx], -1, (0, 180, 0), 2)

        candidates.append({
            "candidate_id": len(candidates) + 1,
            "pixel_area": area,
            "pixel_coordinates": pixel_points,
            "note": "Candidate image contour only; not a verified plot boundary."
        })

    preview_path = output_path / "detected_plots.png"
    if not cv2.imwrite(str(preview_path), preview):
        raise OSError(f"Could not write preview image: {preview_path}")

    candidates_path = output_path / "candidate_boundaries.json"
    with candidates_path.open("w", encoding="utf-8") as handle:
        json.dump(
            {
                "source_image": str(image_path),
                "coordinate_system": "image_pixels",
                "georeferenced": False,
                "candidates": candidates,
                "warning": (
                    "These are image-processing candidates only. "
                    "No GPS, Dag number, ownership, or legal verification is inferred."
                ),
            },
            handle,
            ensure_ascii=False,
            indent=2,
        )

    # Keep the path expected by the existing main.py, but do not invent GPS polygons.
    geojson_path = output_path / "mouza_overlay.geojson"
    geojson_data = {
        "type": "FeatureCollection",
        "features": [],
        "metadata": {
            "georeferenced": False,
            "message": (
                "No verified georeferencing data supplied; map overlay intentionally empty."
            ),
        },
    }
    with geojson_path.open("w", encoding="utf-8") as handle:
        json.dump(geojson_data, handle, ensure_ascii=False, indent=2)

    return {
        "total_candidate_boundaries": len(candidates),
        "processed_image": str(preview_path),
        "candidate_boundaries_file": str(candidates_path),
        "geojson_file": str(geojson_path),
        "geojson": geojson_data,
        "georeferenced": False,
    }


if __name__ == "__main__":
    sample_img = create_dummy_mouza_map()
    result = process_mouza_map(sample_img)
    print(f"Sample image processed. Candidate contours: {result['total_candidate_boundaries']}")
    print("No GPS polygons were created because georeferencing data is unavailable.")