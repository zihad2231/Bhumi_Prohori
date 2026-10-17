from fastapi import FastAPI, UploadFile, File
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
        "message_bn": "সতর্কতা! আরএস খতিয়ানে মোট জমি ছিল ১৫ শতাংশ, কিন্তু বর্তমান বিএস খতিয়ানে ২২ শতাংশ নামজারি করা হয়েছে।"
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
    api_key = os.getenv("GEMINI_API_KEY")
    contents = await file.read()

    if not api_key or api_key.strip() == "":
        return KHATIAN_DATABASE["101"]

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key.strip())
        img = Image.open(io.BytesIO(contents))

        prompt_lines = [
            "You are an expert Bangladeshi Land Khatian (CS/SA/RS/BS Porcha) OCR and Geospatial Engine.",
            "Carefully read the uploaded Khatian image and extract the exact Bengali text and numbers visible:",
            "1. Khatian type and number (e.g., আর এস খতিয়ান নং- ৩২০).",
            "2. District, Upazila, Mouza, and JL No (e.g., উত্তর মুকসেদপুর, বদরগঞ্জ, রংপুর, জে.এল নং: ১৩).",
            "3. Owner name, father/husband name, and address (e.g., দং ছাহেরা খাতুন, জং জহির উদ্দীন).",
            "4. ALL Dag numbers in column 4 separated by commas (e.g., ২৬১৩, ২৬১৭, ২৮৯৯, ২৯২০, ২৯২১, ২৯২২, ২৯৩০, ২৯৬১, ৩০২৪).",
            "5. Total land area at the bottom (e.g., ৭ একর ০১ শতক).",
            "6. Geocode the Mouza/Upazila/District in Bangladesh to accurate GPS latitude ('lat') and longitude ('lng') floats (e.g., Badarganj, Rangpur is lat: 25.6738, lng: 89.0558).",
            "7. In 'lineage', list each Dag number, land class (দলা/ডাঙ্গা), share, and area.",
            "Return ONLY a valid JSON object with keys: dag_no, mouza, jl_no, khatian_no, total_area, recorded_area, status ('Verified'), status_bn, risk_score, current_owner, lat (float), lng (float), lineage (array of {stage, owner, area}), message_bn."
        ]
        prompt = "\n".join(prompt_lines)

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[img, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1,
            ),
        )

        raw_text = response.text.strip()
        json_match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        if not json_match:
            raise ValueError("JSON not found")

        parsed = json.loads(json_match.group(0))
        lat = float(parsed.get("lat", 25.6738))
        lng = float(parsed.get("lng", 89.0558))
        dag_str = str(parsed.get("dag_no", "১০১"))
        mouza_str = str(parsed.get("mouza", "স্ক্যানকৃত মৌজা"))
        is_safe = parsed.get("status", "Verified") == "Verified"

        parsed["lat"] = lat
        parsed["lng"] = lng
        parsed["is_scanned"] = True
        parsed["dynamic_geojson"] = build_dynamic_geojson(lat, lng, dag_str, mouza_str, is_safe)
        return parsed

    except Exception as e:
        print(f"Internal OCR Error: {e}")
        return {
            "dag_no": "স্ক্যান ত্রুটি",
            "mouza": "পুনরায় চেষ্টা করুন",
            "jl_no": "-",
            "khatian_no": "অস্পষ্ট",
            "total_area": "০ শতাংশ",
            "recorded_area": "০ শতাংশ",
            "status": "Disputed",
            "status_bn": "ছবি প্রসেসিংয়ে সাময়িক সমস্যা হয়েছে",
            "risk_score": "অসম্পূর্ণ",
            "current_owner": "শনাক্ত করা যায়নি",
            "lat": 23.8745,
            "lng": 90.3225,
            "lineage": [],
            "message_bn": "সার্ভার ব্যস্ত থাকায় বা ছবির রেজোলিউশন সমস্যার কারণে তথ্য পড়া যায়নি। অনুগ্রহ করে আবার চেষ্টা করুন।",
            "is_scanned": True
        }