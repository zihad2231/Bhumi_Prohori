from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from PIL import Image
import io
import json
import os
import re
import asyncio
from functools import lru_cache
from urllib.parse import urlencode
from urllib.request import Request, urlopen

load_dotenv()

app = FastAPI(title="BhumiProhori AI Service", docs_url=None, redoc_url=None)

# Vite frontend can call this API. Credentials are not needed for this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


def empty_geojson():
    """No official cadastral geometry is available yet."""
    return {"type": "FeatureCollection", "features": []}


def _lookup_mouza_location(query):
    if not query:
        return None

    params = urlencode({
        "q": query,
        "format": "jsonv2",
        "limit": 1,
        "countrycodes": "bd"
    })

    url = f"https://nominatim.openstreetmap.org/search?{params}"
    request = Request(
        url,
        headers={"User-Agent": "BhumiProhori/1.0"}
    )

    try:
        with urlopen(request, timeout=6) as response:
            results = json.loads(response.read().decode("utf-8"))

        if not results:
            return None

        result = results[0]

        return {
            "lat": float(result["lat"]),
            "lng": float(result["lon"]),
            "location_precision": "approximate",
            "location_source": "OpenStreetMap geocoding",
            "location_label": result.get("display_name")
        }

    except Exception:
        return None


async def lookup_mouza_location(mouza, upazila=None, district=None):
    parts = [
        part.strip()
        for part in [mouza, upazila, district, "Bangladesh"]
        if isinstance(part, str) and part.strip()
    ]

    if not mouza or not mouza.strip():
        return None

    query = ", ".join(parts)
    return await asyncio.to_thread(_lookup_mouza_location, query)



@app.get("/")
def health_check():
    return {
        "status": "online",
        "service": "BhumiProhori AI",
        "ocr_configured": bool(os.getenv("GEMINI_API_KEY", "").strip()),
        "official_land_record_verification": "not_configured",
    }


@app.get("/api/mouza-map")
def get_mouza_overlay():
    # Do not generate fake plot boundaries or assign invented dag numbers.
    return empty_geojson()


@app.get("/api/khatian/{dag_no}")
def get_khatian_record(dag_no: str):
    # No official database/API is connected. Never return demo dag 101 for an unknown dag.
    raise HTTPException(
        status_code=404,
        detail=(
            "সরকারি খতিয়ান ডেটাবেস এখনো সংযুক্ত নয়। "
            "এই দাগ নম্বরের সরকারি রেকর্ড এখানে যাচাই করা যাচ্ছে না।"
        ),
    )


@app.post("/api/scan-khatian")
async def scan_khatian_image(file: UploadFile = File(...)):
    """Read visible fields from a Khatian image; OCR is not official verification."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()

    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="GEMINI_API_KEY is not configured on the backend. Set it in Render Environment.",
        )

    if not file.filename:
        raise HTTPException(status_code=400, detail="No file was uploaded.")

    allowed_types = {"image/jpeg", "image/png", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=415,
            detail="Unsupported image format. Upload a JPEG, PNG, or WebP image.",
        )

    try:
        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=400, detail="The uploaded image is empty.")
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Image size must be 10 MB or less.")

        try:
            with Image.open(io.BytesIO(contents)) as check_img:
                check_img.verify()
            with Image.open(io.BytesIO(contents)) as opened_img:
                img_width, img_height = opened_img.size
                opened_img.convert("RGB")
        except Exception as image_error:
            raise HTTPException(
                status_code=400,
                detail="The uploaded file is not a valid image or is corrupted.",
            ) from image_error

        if img_width < 50 or img_height < 50:
            raise HTTPException(status_code=400, detail="Image resolution is too small to read.")

        try:
            from google import genai
            from google.genai import types
        except ImportError as import_error:
            raise HTTPException(
                status_code=500,
                detail="Gemini SDK is missing. Install the google-genai package on Render.",
            ) from import_error

        prompt = """
You are an OCR assistant for Bangladeshi land Khatian/Porcha documents.
Read only text that is visible in the uploaded image. Do not invent or infer
missing values, owner names, area, historical ownership, legal findings, or GPS coordinates.
Return exactly one valid JSON object with these keys:
dag_no,dag_numbers mouza, jl_no, khatian_no, total_area, recorded_area, current_owner,
lineage, lat, lng, status, status_bn, risk_score, message_bn.

Rules:
- dag_no: transcribe all legible dag numbers as a string; otherwise null.
- dag_numbers: return all legible dag numbers as a JSON array of strings; otherwise [].
- mouza: transcribe the visible mouza name; include district/upazila only if visible.
- jl_no, khatian_no, total_area, recorded_area, current_owner: transcribe only if visible; otherwise null.
- lineage: array of {"stage": "...", "owner": "...", "area": "..."} only if printed in the image; otherwise [].
- lat and lng must always be null. Do not infer coordinates from text or image.
- status must be "Pending Verification".
- status_bn must be "সরকারি রেকর্ড যাচাই হয়নি".
- risk_score must be null. Do not assess fraud or legal risk from OCR alone.
- message_bn: briefly summarize the visible OCR result and mention that official verification has not been performed.
- Use null for missing scalar fields. Return JSON only.
"""

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model_name,
            contents=[
                types.Part.from_bytes(data=contents, mime_type=file.content_type),
                prompt,
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1,
            ),
        )

        raw_text = (response.text or "").strip()
        if not raw_text:
            raise ValueError("Gemini returned an empty response.")

        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError:
            cleaned_text = re.sub(
                r"^\s*```(?:json)?\s*|\s*```\s*$",
                "",
                raw_text,
                flags=re.IGNORECASE,
            ).strip()
            parsed = json.loads(cleaned_text)

        if not isinstance(parsed, dict):
            raise ValueError("Gemini response was not a JSON object.")

        defaults = {
            "dag_no": None,
            "dag_numbers": [],
            "mouza": None,
            "jl_no": None,
            "khatian_no": None,
            "total_area": None,
            "recorded_area": None,
            "current_owner": None,
            "lineage": [],
            "lat": None,
            "lng": None,
            "message_bn": "ছবি থেকে তথ্য পড়ার চেষ্টা করা হয়েছে; সরকারি রেকর্ড যাচাই হয়নি।",
        }
        for key, value in defaults.items():
            parsed.setdefault(key, value)

        if not isinstance(parsed.get("lineage"), list):
            parsed["lineage"] = []

        if not isinstance(parsed.get("dag_numbers"), list):
            parsed["dag_numbers"] = []

        if not parsed["dag_numbers"] and parsed.get("dag_no"):
            parsed["dag_numbers"] = [parsed["dag_no"]]

        if not parsed.get("dag_no") and parsed["dag_numbers"]:
            parsed["dag_no"] = ", ".join(
                str(number) for number in parsed["dag_numbers"]
            )

        # Force non-verification status. OCR cannot confirm ownership or fraud.
        parsed["status"] = "Pending Verification"
        parsed["status_bn"] = "সরকারি রেকর্ড যাচাই হয়নি"
        parsed["risk_score"] = None
        parsed["lat"] = None
        parsed["lng"] = None

        location = await lookup_mouza_location(parsed.get("mouza"))

        if location:
            parsed.update(location)
        else:
            parsed["location_precision"] = None
            parsed["location_source"] = None
            parsed["location_label"] = None

        parsed["is_scanned"] = True
        parsed["verification_source"] = "OCR only; no official land-record API connected"
        parsed["dynamic_geojson"] = empty_geojson()
        return parsed

    except HTTPException:
        raise
    except Exception as error:
        print(f"KHATIAN OCR ERROR ({type(error).__name__}): {error}")
        error_text = str(error)
        if "404" in error_text or "NOT_FOUND" in error_text or "not found" in error_text.lower():
            detail = (
                f"Gemini model '{model_name}' was not found or is unavailable. "
                "Check GEMINI_MODEL in Render Environment."
            )
            status_code = 502
        elif "API_KEY_INVALID" in error_text or "invalid api key" in error_text.lower():
            detail = "Gemini API key is invalid. Check GEMINI_API_KEY in Render Environment."
            status_code = 502
        else:
            detail = "খতিয়ান স্ক্যান করা যায়নি। Render-এর backend logs পরীক্ষা করে আবার চেষ্টা করুন।"
            status_code = 502
        raise HTTPException(status_code=status_code, detail=detail) from error
    finally:
        await file.close()