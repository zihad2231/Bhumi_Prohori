import cv2
import numpy as np
import json
import os

# Base GPS Coordinates for Daffodil Smart City (Ashulia) area (Latitude, Longitude)
BASE_LAT = 23.8765
BASE_LNG = 90.3201

def create_dummy_mouza_map(filepath="processed_data/sample_mouza.png"):
    """Generates a synthetic Mouza map image with 4 land plots for testing."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    # Create a white canvas (600x600 pixels)
    img = np.ones((600, 600, 3), dtype=np.uint8) * 255

    # Define 4 polygon land plots (Dag) with black boundaries
    plots = [
        [(50, 50), (280, 50), (270, 260), (50, 250)],    # Plot/Dag No 101
        [(290, 50), (550, 60), (540, 270), (280, 260)],  # Plot/Dag No 102
        [(50, 270), (270, 280), (260, 540), (60, 530)],  # Plot/Dag No 103
        [(280, 280), (540, 290), (530, 550), (275, 540)] # Plot/Dag No 104
    ]

    for poly in plots:
        pts = np.array(poly, np.int32).reshape((-1, 1, 2))
        cv2.polylines(img, [pts], isClosed=True, color=(0, 0, 0), thickness=3)

    cv2.imwrite(filepath, img)
    return filepath

def process_mouza_map(image_path: str, output_dir="processed_data"):
    """Detects plot boundaries from a Mouza map using OpenCV and exports GeoJSON."""
    os.makedirs(output_dir, exist_ok=True)
    
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError("Input image not found or unreadable.")

    # 1. Convert to Grayscale and apply Gaussian Blur for noise reduction
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # 2. Canny Edge Detection and Morphological Closing
    edges = cv2.Canny(blurred, 50, 150)
    kernel = np.ones((3, 3), np.uint8)
    closed_edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

    # 3. Extract external contours representing land plots
    contours, _ = cv2.findContours(closed_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    output_img = img.copy()
    features = []
    dag_start = 101

    for cnt in contours:
        area = cv2.contourArea(cnt)
        # Filter out small noise artifacts and retain valid land plots
        if area > 5000:
            # Douglas-Peucker algorithm to approximate contour into a clean polygon
            epsilon = 0.02 * cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, epsilon, True)

            # Draw green boundary on the output image for visual verification
            cv2.drawContours(output_img, [approx], -1, (0, 180, 0), 3)

            # Transform pixel coordinates into GPS (Lat/Lng) GeoJSON coordinates
            geo_coords = []
            for pt in approx:
                px, py = pt[0]
                lng = BASE_LNG + (px * 0.000008)
                lat = BASE_LAT - (py * 0.000008)
                geo_coords.append([round(lng, 6), round(lat, 6)])
            
            # Close the polygon ring by repeating the first coordinate at the end
            geo_coords.append(geo_coords[0])

            features.append({
                "type": "Feature",
                "properties": {
                    "dag_no": str(dag_start),
                    "estimated_area_pixel": area,
                    "status": "Verified" if dag_start != 102 else "Disputed (Over-mutation)"
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [geo_coords]
                }
            })
            dag_start += 1

    # 4. Save processed image and GeoJSON output
    processed_img_path = os.path.join(output_dir, "detected_plots.png")
    geojson_path = os.path.join(output_dir, "mouza_overlay.geojson")

    cv2.imwrite(processed_img_path, output_img)

    geojson_data = {
        "type": "FeatureCollection",
        "features": features
    }

    with open(geojson_path, "w", encoding="utf-8") as f:
        json.dump(geojson_data, f, indent=2, ensure_ascii=False)

    return {
        "total_plots_detected": len(features),
        "processed_image": processed_img_path,
        "geojson_file": geojson_path,
        "geojson": geojson_data
    }

if __name__ == "__main__":
    sample_img = create_dummy_mouza_map()
    result = process_mouza_map(sample_img)
    print(f"Success! Total plots detected: {result['total_plots_detected']}")
    print(f"GeoJSON saved to: {result['geojson_file']}")