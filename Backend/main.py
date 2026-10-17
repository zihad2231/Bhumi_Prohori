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

app = FastAPI(title="BhumiProhori AI Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def build_dynamic_geojson(lat: float, lng: float, dag_list_str: str, mouza_name: str, is_safe: bool = True):
    """Generates dynamic interactive Mouza plot polygons around the scanned location's GPS coordinates."""
    raw_dags = [d.strip() for d in re.split(r"[,،/|-]+", dag_list_str) if d.strip()]
    if not raw_dags:
        raw_dags = [dag_list_str]

    features = []
    cols = 3
    size = 0.0008
    gap = 0.00015

    for idx, dag in enumerate(raw_dags[:9]):  # Up to 9 plots from the Khatian
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

# Pre-configured sample records
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
    return {"status": "online", "service": "BhumiProhori AI v2.0"}

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

    if not api_key or api_key.strip() == "" or api_key == "your_api_key_here":
        return {
            "dag_no": "কনফিগারেশন ত্রুটি",
            "mouza": "সার্ভার সেটআপ প্রয়োজন",
            "jl_no": "-",
            "khatian_no": "পাওয়া যায়নি",
            "total_area": "০ শতাংশ",
            "recorded_area": "০ শতাংশ",
            "status": "Disputed",
            "status_bn": "সার্ভারে এআই সার্ভিস কি (Key) সক্রিয় নেই",
            "risk_score": "ত্রুটি",
            "current_owner": "Render Environment চেক করুন",
            "lat": 23.8745,
            "lng": 90.3225,
            "lineage": [],
            "message_bn": "সার্ভারে এআই ভিশন কনফিগারেশন পাওয়া যায়নি। Render ড্যাশবোর্ডে Environment ভেরিয়েবল যুক্ত করে পুনরায় ডিপ্লয় করুন।",
            "is_scanned": True
        }

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key.strip())
        img = Image.open(io.BytesIO(contents))

        prompt = """
        You are an advanced Bangladeshi Land Khatian (CS/SA/RS/BS Porcha) OCR and Geospatial Intelligence Engine.
        Carefully examine the uploaded Khatian image and extract the exact Bengali information written on it:
        1. খতিয়ানের ধরন ও নম্বর (e.g., আর এস খতিয়ান নং- ৩২০).
        2. জেলা, থানা/উপজেলা, মৌজা ও জে.এল নং (e.g., জেলা: রংপুর, উপজেলা: বদরগঞ্জ, মৌজা: উত্তর মুকসেদপুর, জে.এল নং: ১৩).
        3. মালিকের নাম, পিতা/স্বামীর নাম ও ঠিকানা (e.g., দং ছাহেরা খাতুন, জং জহির উদ্দীন, সাং দঃ মকছুদপুর).
        4. সকল দাগ নম্বর (If there are multiple Dag numbers in column 4 like ২৬১৩, ২৬১৭, ২৮৯৯, ২৯২০, ২৯২১, ২৯২২, ২৯৩০, ২৯৬১, ৩০২৪, list ALL of them separated by commas).
        5. মোট জমি (Look at the bottom 'মোট জমি' row, e.g., ৭ একর ০১ শতক বা ৭০১ শতক).
        6. Geocode the extracted Mouza, Upazila, and District in Bangladesh to its accurate real-world GPS latitude ('lat') and longitude ('lng') as float numbers (for example, Badarganj, Rangpur is around lat: 25.6738, lng: 89.0558).
        7. In 'lineage', list each individual Dag number, its land class (জমির শ্রেণী যেমন দলা/ডাঙ্গা), and its area so the user sees the full breakdown!

        Return ONLY a valid JSON object matching this exact schema:
        {
          "dag_no": "কমা দিয়ে সকল দাগ নম্বর (যেমন: ২৬১৩, ২৬১৭, ২৮৯৯, ২৯২০...)",
          "mouza": "মৌজা, উপজেলা ও জেলার নাম (যেমন: উত্তর মুকসেদপুর, বদরগঞ্জ, রংপুর)",
          "jl_no": "জে.এল নম্বর (যেমন: ১৩)",
          "khatian_no": "খতিয়ান নম্বর ও ধরন (যেমন: ৩২০ - আর এস)",
          "total_area": "খতিয়ানের সর্বমোট জমি (যেমন: ৭ একর ০১ শতক / ৭০১ শতক)",
          "recorded_area": "মালিকের অংশ ও মোট পরিমাণ (যেমন: পূর্ণ অংশ - ৭ একর ০১ শতক)",
          "status": "Verified",
          "status_bn": "এআই (AI) দ্বারা খতিয়ান সফলভাবে শনাক্ত ও যাচাইকৃত",
          "risk_score": "৩% (সার্টিফাইড কপি)",
          "current_owner": "মালিকের সম্পূর্ণ নাম ও পরিচয়",
          "lat": 25.6738,
          "lng": 89.0558,
          "lineage": [
            {"stage": "দাগ নং ২৬১৩ (দলা)", "owner": "মালিকের অংশ: ১.০০০", "area": "৪৪ শতক"},
            {"stage": "দাগ নং ২৬১৭ (দলা)", "owner": "মালিকের অংশ: ১.০০০", "area": "১ একর ২৩ শতক"}
          ],
          "message_bn": "খতিয়ানটির জেলা, মৌজা, সকল দাগ নম্বর এবং মোট জমির পরিমাণ স্বয়ংক্রিয়ভাবে যাচাই করা হয়েছে এবং স্যাটে