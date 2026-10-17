from fastapi import FastAPI, UploadFile, File, HTTPException

from fastapi.middleware.cors import CORSMiddleware

import json

import os

import re

import io

from dotenv import load_dotenv

from PIL import Image

from cv_engine import create_dummy_mouza_map, process_mouza_map



load_dotenv()



app = FastAPI(title="BhumiProhori AI Service", docs_url=None, redoc_url=None)



app.add_middleware(

       CORSMiddleware,

       allow_origins=["*"],

       allow_credentials=True,

       allow_methods=["*"],

       allow_headers=["*"],

)





def build_dynamic_geojson(lat: float, lng: float, dag_list_str: str, mouza_name: str, is_safe: bool = True):

       raw_dags = [d.strip() for d in re.split(r"[,،/|-]+", dag_list_str) if d.strip()]

       if not raw_dags:

           raw_dags = [dag_list_str]



       features = []

       cols = 3

       size = 0.0008

       gap = 0.00015



       for idx, dag in enumerate(raw_dags[:9]):

           r = idx // cols

           c = idx % cols

           lon1 = lng - 0.0012 + c * (size + gap)

           lat1 = lat + 0.0008 - r * (size + gap)

           lon2 = lon1 + size

           lat2 = lat1 - size



           features.append({

               "type": "Feature",

               "properties": {

                   "dag_no": dag,

                   "mouza": mouza_name,

                   "status": "Verified" if is_safe else "Disputed"

               },

               "geometry": {

                   "type": "Polygon",

                   "coordinates": [[

                       [lon1, lat1],

                       [lon2, lat1],

                       [lon2, lat2],

                       [lon1, lat2],

                       [lon1, lat1]

                   ]]

               }

           })



       return {"type": "FeatureCollection", "features": features}





KHATIAN_DATABASE = {

       "101": {

           "dag_no": "১০১",

           "mouza": "আশুলিয়া, সাভার, ঢাকা",

           "jl_no": "১৪",

           "khatian_no": "৪৫২ (বিএস)",

           "total_area": "২০.০০ শতাংশ",

           "recorded_area": "২০.০০ শতাংশ",

           "status": "Verified",

           "status_bn": "সম্পূর্ণ নিরাপদ ও যাচাইকৃত",

           "risk_score": "৫% (ঝুঁকিমুক্ত)",

           "current_owner": "মোঃ আব্দুল করিম",

           "lat": 23.8755,

           "lng": 90.3215,

           "lineage": [

               {"stage": "CS (১৯৪০)", "owner": "হাজী জমির উদ্দিন", "area": "২০ শতাংশ"},

               {"stage": "SA (১৯৬২)", "owner": "আব্দুর রহমান (ওয়ারিশ)", "area": "২০ শতাংশ"},

               {"stage": "RS (১৯৮০)", "owner": "আব্দুর রহমান", "area": "২০ শতাংশ"},

               {"stage": "BS (বর্তমান)", "owner": "মোঃ আব্দুল করিম (ক্রয়সূত্রে)", "area": "২০ শতাংশ"}

           ],

           "message_bn": "সিএস থেকে বিএস পর্যন্ত খতিয়ানের সকল হিসাব ও মালিকানার ধারাবাহিকতা ১০০% সঠিক আছে। জমিটি কেনার জন্য নিরাপদ।"

       },

       "102": {

           "dag_no": "১০২",

           "mouza": "আশুলিয়া, সাভার, ঢাকা",

           "jl_no": "১৪",

           "khatian_no": "৭৮৯ (বিএস)",

           "total_area": "১৫.০০ শতাংশ",

           "recorded_area": "২২.০০ শতাংশ (অতিরিক্ত ৭ শতক!)",

           "status": "Disputed",

           "status_bn": "জালিয়াতি সতর্কতা! (অতিরিক্ত নামজারি)",

           "risk_score": "৯২% (অত্যন্ত ঝুঁকিপূর্ণ)",

           "current_owner": "রফিকুল ইসলাম ও অন্যান্য",

           "lat": 23.8755,

           "lng": 90.3235,

           "lineage": [

               {"stage": "CS (১৯৪০)", "owner": "কালিপদ সাহা", "area": "১৫ শতাংশ"},

               {"stage": "SA (১৯৬২)", "owner": "মনোরঞ্জন সাহা", "area": "১৫ শতাংশ"},

               {"stage": "RS (১৯৮০)", "owner": "সুলতান মাহমুদ", "area": "১৫ শতাংশ"},

               {"stage": "BS (বর্তমান)", "owner": "রফিকুল ইসলাম গং (জাল খতিয়ান সন্দেহ)", "area": "২২ শতাংশ"}

           ],

           "message_bn": "সতর্কতা! আরএস খতিয়ানে মোট জমি ছিল ১৫ শতাংশ, কিন্তু বর্তমান বিএস খতিয়ানে ২২ শতাংশ নামজারি করা হয়েছে। এখানে ৭ শতাংশ জমির জালিয়াতি শনাক্ত হয়েছে!"

       },

       "103": {

           "dag_no": "১০৩",

           "mouza": "আশুলিয়া, সাভার, ঢাকা",

           "jl_no": "১৪",

           "khatian_no": "৫১০ (বিএস)",

           "total_area": "৩০.০০ শতাংশ",

           "recorded_area": "৩০.০০ শতাংশ",

           "status": "Verified",

           "status_bn": "সম্পূর্ণ নিরাপদ ও যাচাইকৃত",

           "risk_score": "৮% (ঝুঁকিমুক্ত)",

           "current_owner": "মিসেস সালমা বেগম",

           "lat": 23.8735,

           "lng": 90.3215,

           "lineage": [

               {"stage": "CS (১৯৪০)", "owner": "আফসার উদ্দিন", "area": "৩০ শতাংশ"},

               {"stage": "SA (১৯৬২)", "owner": "হাবিবুর রহমান", "area": "৩০ শতাংশ"},

               {"stage": "RS (১৯৮০)", "owner": "হাবিবুর রহমান", "area": "৩০ শতাংশ"},

               {"stage": "BS (বর্তমান)", "owner": "মিসেস সালমা বেগম", "area": "৩০ শতাংশ"}

           ],

           "message_bn": "মালিকানার চেইন এবং মৌজা ম্যাপের সীমানা সঠিক রয়েছে। কোনো সীমানা বিরোধ বা মামলা পাওয়া যায়নি।"

       },

       "104": {

           "dag_no": "১০৪",

           "mouza": "আশুলিয়া, সাভার, ঢাকা",

           "jl_no": "১৪",

           "khatian_no": "৬১২ (বিএস)",

           "total_area": "১২.৫০ শতাংশ",

           "recorded_area": "১২.৫০ শতাংশ",

           "status": "Verified",

           "status_bn": "সম্পূর্ণ নিরাপদ ও যাচাইকৃত",

           "risk_score": "১০% (ঝুঁকিমুক্ত)",

           "current_owner": "ক্যাপ্টেন ডেভেলপার্স লিঃ",

           "lat": 23.8735,

           "lng": 90.3235,

           "lineage": [

               {"stage": "CS (১৯৪০)", "owner": "জব্বার আলী", "area": "১২.৫০ শতাংশ"},

               {"stage": "SA (১৯৬২)", "owner": "আনোয়ার হোসেন", "area": "১২.৫০ শতাংশ"},

               {"stage": "RS (১৯৮০)", "owner": "আনোয়ার হোসেন", "area": "১২.৫০ শতাংশ"},

               {"stage": "BS (বর্তমান)", "owner": "ক্যাপ্টেন ডেভেলপার্স লিঃ", "area": "১২.৫০ শতাংশ"}

           ],

           "message_bn": "খতিয়ান ও স্যাটেলাইট ম্যাপের সীমানা সম্পূর্ণ মিলে গেছে। জমিটি শতভাগ নিরাপদ।"

       }

}





@app.get("/")

def health_check():

       return {"status": "online", "service": "BhumiProhori AI"}





@app.get("/api/mouza-map")

def get_mouza_overlay():

       geojson_path = "processed_data/mouza_overlay.geojson"

       if not os.path.exists(geojson_path):

           sample_img = create_dummy_mouza_map()

           process_mouza_map(sample_img)



       with open(geojson_path, "r", encoding="utf-8") as f:

           data = json.load(f)

       return data





@app.get("/api/khatian/{dag_no}")

def verify_dag_record(dag_no: str):

       return KHATIAN_DATABASE.get(dag_no, KHATIAN_DATABASE["101"])





@app.post("/api/scan-khatian")
async def scan_khatian_image(file: UploadFile = File(...)):
    """Extract visible fields from a Khatian image using Gemini.

    OCR output is not proof of legal ownership or official verification.
    """
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

        # Validate image bytes, then reopen for processing.
        try:
            with Image.open(io.BytesIO(contents)) as check_img:
                check_img.verify()
            with Image.open(io.BytesIO(contents)) as opened_img:
                img = opened_img.convert("RGB")
        except Exception as image_error:
            raise HTTPException(
                status_code=400,
                detail="The uploaded file is not a valid image or is corrupted.",
            ) from image_error

        if img.width < 50 or img.height < 50:
            raise HTTPException(status_code=400, detail="Image resolution is too small to read.")

        try:
            from google import genai
            from google.genai import types
        except ImportError as import_error:
            print(f"Gemini SDK import error: {import_error}")
            raise HTTPException(
                status_code=500,
                detail="Gemini SDK is missing. Install the google-genai package on Render.",
            ) from import_error

        prompt = """
You are an OCR assistant for Bangladeshi land Khatian documents.
Read only information visible in the uploaded image. Never invent missing
names, measurements, historical ownership, legal findings, or coordinates.
Return one valid JSON object with these keys:
 dag_no, mouza, jl_no, khatian_no, total_area, recorded_area,
 status, status_bn, risk_score, current_owner, lat, lng, lineage, message_bn.

Rules:
- dag_no: all legible Dag numbers, comma-separated.
- mouza: Mouza name; include district/upazila only if supported by the document.
- jl_no and khatian_no: transcribe if readable, otherwise null.
- total_area and recorded_area: transcribe the relevant area values if visible.
- current_owner: transcribe the name if readable, otherwise null.
- lineage: array of {"stage": ..., "owner": ..., "area": ...}; use [] if not shown.
- lat and lng: use null. Do not infer geographic coordinates from the document alone.
- risk_score: null unless a separate, real verification process provides evidence.
- status: "Pending Verification".
- status_bn: "সরকারি রেকর্ড যাচাই প্রয়োজন".
- message_bn: briefly describe OCR result and unreadable/missing fields in Bangla.
- Use null for missing scalar values. Do not claim that the land is legally verified
  or safe to buy. Return JSON only.
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

        # JSON mode should return JSON directly; tolerate Markdown fences as fallback.
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

        # Ensure consistent fields for the frontend.
        defaults = {
            "dag_no": None,
            "mouza": None,
            "jl_no": None,
            "khatian_no": None,
            "total_area": None,
            "recorded_area": None,
            "current_owner": None,
            "risk_score": None,
            "lineage": [],
            "message_bn": "ছবি থেকে তথ্য পড়া হয়েছে; সরকারি রেকর্ড যাচাই প্রয়োজন।",
        }
        for key, value in defaults.items():
            parsed.setdefault(key, value)

        if not isinstance(parsed.get("lineage"), list):
            parsed["lineage"] = []

        # OCR alone cannot establish legal verification or a risk score.
        parsed["status"] = "Pending Verification"
        parsed["status_bn"] = "সরকারি রেকর্ড যাচাই প্রয়োজন"
        parsed["risk_score"] = None

        # Only use coordinates if an independently trusted source supplies them.
        # The prompt asks Gemini to return null rather than guess them.
        lat = parsed.get("lat")
        lng = parsed.get("lng")
        try:
            lat = float(lat)
            lng = float(lng)
            if not (-90 <= lat <= 90 and -180 <= lng <= 180):
                raise ValueError("Coordinates out of range")
        except (TypeError, ValueError):
            lat = None
            lng = None

        parsed["lat"] = lat
        parsed["lng"] = lng
        parsed["is_scanned"] = True

        if lat is not None and lng is not None:
            parsed["dynamic_geojson"] = build_dynamic_geojson(
                lat,
                lng,
                str(parsed.get("dag_no") or ""),
                str(parsed.get("mouza") or ""),
                is_safe=False,
            )
        else:
            parsed["dynamic_geojson"] = {
                "type": "FeatureCollection",
                "features": [],
            }

        return parsed

    except HTTPException:
        raise
    except Exception as error:
        error_text = str(error)
        print(f"KHATIAN GEMINI ERROR ({type(error).__name__}): {error_text}")

        # Keep provider details in server logs; return a useful message to the UI.
        if "404" in error_text or "NOT_FOUND" in error_text or "not found" in error_text.lower():
            detail = (
                f"Gemini model '{model_name}' was not found or is unavailable for this API key. "
                "Check the model name and available models for your Gemini API project. "
                "You can set GEMINI_MODEL in Render Environment."
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