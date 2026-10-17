import React, { useState, useEffect } from "react";
import {
  MapContainer,
  TileLayer,
  GeoJSON,
  Marker,
  Popup,
  useMap,
  useMapEvents,
} from "react-leaflet";
import L from "leaflet";
import {
  ShieldCheck,
  AlertTriangle,
  Upload,
  MapPin,
  FileText,
  GitBranch,
  Search,
  Printer,
  CheckCircle2,
  Sparkles,
  PhoneCall,
  Layers,
  Crosshair,
  RefreshCw,
} from "lucide-react";

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

const API_BASE = import.meta.env.VITE_API_BASE_URL || "https://bhumi-prohori.onrender.com";

const PLOT_COORDS = {}; // No demo Dag coordinates: real coordinates must be supplied or selected by the user.

function MapClickSelector({ onLocationSelect }) {
  useMapEvents({
    click(event) {
      onLocationSelect(event.latlng.lat, event.latlng.lng);
    },
  });

  return null;
}

function MapController({ center, zoom }) {
  const map = useMap();

  useEffect(() => {
    const timer = setTimeout(() => {
      map.invalidateSize();
    }, 250);
    return () => clearTimeout(timer);
  }, [map]);

  useEffect(() => {
    if (center && center.length === 2) {
      map.invalidateSize();
      map.flyTo(center, zoom, { duration: 1.5 });
    }
  }, [center, zoom, map]);

  return null;
}

export default function App() {
  const [defaultGeoData, setDefaultGeoData] = useState(null);
  const [activeGeoData, setActiveGeoData] = useState(null);
  const [showOverlay, setShowOverlay] = useState(true);
  const [mapType, setMapType] = useState("hybrid");
  const [selectedDag, setSelectedDag] = useState(null);
  const [khatianInfo, setKhatianInfo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [isCustomScan, setIsCustomScan] = useState(false);
  const [uploadedPreview, setUploadedPreview] = useState(null);
  const [mapCenter, setMapCenter] = useState([23.6850, 90.3563]);
  const [mapZoom, setMapZoom] = useState(7);
  const [userGps, setUserGps] = useState(null);
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [latitudeInput, setLatitudeInput] = useState("");
  const [longitudeInput, setLongitudeInput] = useState("");
  const [coordinateError, setCoordinateError] = useState("");

  useEffect(() => {
    fetch(`${API_BASE}/api/mouza-map`)
      .then((res) => res.json())
      .then((data) => {
        setDefaultGeoData(data);
        setActiveGeoData(data);
      })
      .catch(() => {});
  }, []);

  const handleSelectPredefinedDag = (dagId) => {
    setIsCustomScan(false);
    setUploadedPreview(null);
    setSelectedDag(dagId);
    if (defaultGeoData) {
      setActiveGeoData(defaultGeoData);
    }
    if (PLOT_COORDS[dagId]) {
      setMapCenter(PLOT_COORDS[dagId]);
      setMapZoom(17);
    }

    setLoading(true);
    fetch(`${API_BASE}/api/khatian/${dagId}`)
      .then((res) => res.json())
      .then((data) => {
        setKhatianInfo(data);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
      });
  };

  // Upload Khatian Image -> Extract Real Info -> Track Location on Satellite Map
  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const previewUrl = URL.createObjectURL(file);
    setUploadedPreview(previewUrl);
    setIsCustomScan(true);
    setLoading(true);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${API_BASE}/api/scan-khatian`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) {
        setKhatianInfo({
          is_scanned: false,
          status: "Scan Failed",
          status_bn: "খতিয়ান স্ক্যান করা যায়নি",
          risk_score: null,
          message_bn: data.detail || "OCR সার্ভার থেকে তথ্য পাওয়া যায়নি। Render backend logs পরীক্ষা করুন।",
          dag_no: null,
          mouza: null,
          jl_no: null,
          khatian_no: null,
          total_area: null,
          recorded_area: null,
          current_owner: null,
          lineage: [],
          lat: null,
          lng: null,
        });
        setActiveGeoData({ type: "FeatureCollection", features: [] });
        return;
      }
      setKhatianInfo(data);

      // OCR does not establish land location; only use coordinates if a trusted source explicitly supplies them.
      if (
        data.lat !== undefined && data.lat !== null &&
        data.lng !== undefined && data.lng !== null &&
        Number.isFinite(Number(data.lat)) && Number.isFinite(Number(data.lng)) &&
        Number(data.lat) >= -90 && Number(data.lat) <= 90 &&
        Number(data.lng) >= -180 && Number(data.lng) <= 180
      ) {
        const coords = [Number(data.lat), Number(data.lng)];
        setMapCenter(coords);
        setMapZoom(17);
        setSelectedLocation(coords);
        setLatitudeInput(coords[0].toFixed(7));
        setLongitudeInput(coords[1].toFixed(7));
      }

      // Never treat OCR output as cadastral geometry. The backend currently returns no official boundaries.
      setActiveGeoData({ type: "FeatureCollection", features: [] });
    } catch {
      setKhatianInfo({
        is_scanned: false,
        status: "Scan Failed",
        status_bn: "সার্ভারের সঙ্গে সংযোগ করা যায়নি",
        risk_score: null,
        message_bn: "নেটওয়ার্ক বা backend সংযোগে সমস্যা হয়েছে। Render-এর backend logs পরীক্ষা করে আবার চেষ্টা করুন।",
        dag_no: null,
        mouza: null,
        jl_no: null,
        khatian_no: null,
        total_area: null,
        recorded_area: null,
        current_owner: null,
        lineage: [],
        lat: null,
        lng: null,
      });
      setActiveGeoData({ type: "FeatureCollection", features: [] });
    } finally {
      setLoading(false);
      e.target.value = null;
    }
  };

  const handleLocateMe = () => {
    if (!navigator.geolocation) {
      alert("আপনার ব্রাউজারে জিপিএস (Geolocation) সাপোর্ট করছে না।");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const coords = [pos.coords.latitude, pos.coords.longitude];
        setUserGps(coords);
        setSelectedLocation(coords);
        setLatitudeInput(coords[0].toFixed(7));
        setLongitudeInput(coords[1].toFixed(7));
        setCoordinateError("");
        setMapCenter(coords);
        setMapZoom(18);
      },
      () => {
        alert("জিপিএস লোকেশন পাওয়া যায়নি। ব্রাউজারে Location Permission চালু করুন।");
      }
    );
  };

  const handleCoordinateSearch = (e) => {
    e.preventDefault();

    const latText = latitudeInput.trim();
    const lngText = longitudeInput.trim();
    const lat = Number(latText);
    const lng = Number(lngText);

    if (
      !latText || !lngText ||
      !Number.isFinite(lat) || !Number.isFinite(lng) ||
      lat < -90 || lat > 90 || lng < -180 || lng > 180
    ) {
      setCoordinateError("সঠিক Latitude (-90 থেকে 90) এবং Longitude (-180 থেকে 180) লিখুন।");
      return;
    }

    const coords = [lat, lng];
    setCoordinateError("");
    setSelectedLocation(coords);
    setLatitudeInput(lat.toFixed(7));
    setLongitudeInput(lng.toFixed(7));
    setMapCenter(coords);
    setMapZoom(18);
  };

  const handleMapLocationSelect = (lat, lng) => {
    const coords = [lat, lng];
    setSelectedLocation(coords);
    setLatitudeInput(lat.toFixed(7));
    setLongitudeInput(lng.toFixed(7));
    setCoordinateError("");
    setMapCenter(coords);
  };

  const plotStyle = (feature) => {
    const isDisputed =
      feature.properties.dag_no === "102" || feature.properties.status === "Disputed";
    const isSelected = !isCustomScan && feature.properties.dag_no === selectedDag;
    return {
      fillColor: isDisputed ? "#ef4444" : "#10b981",
      weight: isCustomScan || isSelected ? 3 : 2,
      opacity: 1,
      color: isCustomScan || isSelected ? "#fbbf24" : "#ffffff",
      fillOpacity: 0.55,
    };
  };

  const onEachPlot = (feature, layer) => {
    const dag = feature.properties.dag_no;
    let label = `দাগ নং: ${dag}`;
    if (!isCustomScan) {
      if (dag === "101") label = "দাগ নং: ১০১";
      if (dag === "102") label = "দাগ নং: ১০২ (ঝুঁকিপূর্ণ)";
      if (dag === "103") label = "দাগ নং: ১০৩";
      if (dag === "104") label = "দাগ নং: ১০৪";
    }

    layer.bindTooltip(label, {
      permanent: true,
      direction: "center",
      className: "leaflet-tooltip-own",
    });

    layer.on({
      click: () => {
        if (!isCustomScan) {
          handleSelectPredefinedDag(dag);
        }
      },
    });
  };

  const isSafe = khatianInfo && khatianInfo.status === "Verified";
  const lineageList = Array.isArray(khatianInfo?.lineage) ? khatianInfo.lineage : [];

  return (
    <div className="min-h-screen flex flex-col bg-slate-100 text-slate-800">
      {/* Header */}
      <header className="bg-gradient-to-r from-emerald-950 via-emerald-900 to-teal-900 text-white shadow-xl sticky top-0 z-50 border-b border-emerald-700/50">
        <div className="max-w-7xl mx-auto px-4 py-3 flex flex-wrap justify-between items-center gap-4">
          <div className="flex items-center gap-3.5">
            <div className="relative flex items-center justify-center w-12 h-12 rounded-2xl bg-gradient-to-br from-amber-400 via-emerald-400 to-teal-600 p-0.5 shadow-lg">
              <div className="w-full h-full bg-emerald-950 rounded-xl flex items-center justify-center">
                <svg viewBox="0 0 64 64" className="w-8 h-8" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M32 5L9 14.5V30.5C9 45.8 18.8 58.3 32 62C45.2 58.3 55 45.8 55 30.5V14.5L32 5Z" fill="#065f46" stroke="#34d399" strokeWidth="3"/>
                  <path d="M15 28H49M17 40H47M32 14V55" stroke="#a7f3d0" strokeWidth="1.5" strokeOpacity="0.6" strokeDasharray="3 2"/>
                  <circle cx="32" cy="27" r="7" fill="#fbbf24"/>
                  <circle cx="32" cy="27" r="3" fill="#064e3b"/>
                  <path d="M24 45L29.5 50.5L41 39" stroke="#fbbf24" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2.5">
                <h1 className="text-2xl md:text-3xl font-extrabold tracking-wide text-white">ভূমি-প্রহরী এআই</h1>
                <span className="text-xs bg-amber-400/20 text-amber-300 border border-amber-400/40 px-2.5 py-0.5 rounded-full font-bold flex items-center gap-1">
                  <Sparkles className="w-3 h-3" /> BhumiProhori AI
                </span>
              </div>
              <p className="text-xs md:text-sm text-emerald-200 font-medium">
                এক ক্লিকেই মৌজা ম্যাপ, জমির সীমানা ও আসল-নকল খতিয়ান যাচাই করুন
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <label className="cursor-pointer bg-amber-400 hover:bg-amber-300 text-slate-950 font-extrabold px-5 py-2.5 rounded-xl shadow-lg flex items-center gap-2 transition transform hover:-translate-y-0.5 text-sm md:text-base">
              <Upload className="w-5 h-5" />
              <span>খতিয়ান বা পর্চার ছবি আপলোড করুন</span>
              <input type="file" accept="image/*" onChange={handleFileUpload} className="hidden" />
            </label>
          </div>
        </div>
      </header>

      {/* Top Instruction Bar */}
      <div className="bg-emerald-900/10 border-b border-emerald-800/15">
        <div className="max-w-7xl mx-auto px-4 py-2.5 flex flex-wrap items-center justify-between gap-2 text-xs md:text-sm text-emerald-950 font-semibold">
          <div className="flex flex-wrap items-center gap-3">
            <span className="bg-emerald-700 text-white px-2.5 py-0.5 rounded-md font-bold">সহজ নির্দেশনা:</span>
            <span>১. যেকোনো খতিয়ানের ছবি আপলোড করলে এআই দৃশ্যমান তথ্য পড়ার চেষ্টা করবে; প্রকৃত জমির অবস্থান আলাদাভাবে যাচাই করতে হবে</span>
          </div>
          <span className="text-emerald-800 font-bold flex items-center gap-1">
            <PhoneCall className="w-3.5 h-3.5" /> ভূমি সহায়তা হটলাইন: ১৬১২২
          </span>
        </div>
      </div>

      {/* Plot Selection & Map Controls Bar */}
      <div className="bg-white border-b shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-3.5 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-2.5 flex-wrap">
            <span className="font-bold text-slate-800 flex items-center gap-1.5 text-base">
              <Search className="w-5 h-5 text-emerald-600" /> দাগ নম্বর:
            </span>
            {[
            ].map((item) => (
              <button
                key={item.id}
                onClick={() => handleSelectPredefinedDag(item.id)}
                className={`px-4 py-2 rounded-xl font-bold text-sm transition-all shadow-sm ${
                  !isCustomScan && selectedDag === item.id
                    ? item.id === "102"
                      ? "bg-red-600 text-white ring-4 ring-red-200"
                      : "bg-emerald-600 text-white ring-4 ring-emerald-200"
                    : "bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-300"
                }`}
              >
                {item.label}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            <form
              onSubmit={handleCoordinateSearch}
              className="flex flex-wrap items-end gap-2 rounded-xl border border-blue-200 bg-blue-50 p-2"
            >
              <label className="text-xs font-bold text-slate-700">
                Latitude
                <input
                  type="number"
                  step="any"
                  value={latitudeInput}
                  onChange={(e) => setLatitudeInput(e.target.value)}
                  placeholder="23.8103"
                  className="mt-1 block w-28 rounded-lg border border-slate-300 bg-white px-2 py-1.5 font-normal"
                  required
                />
              </label>
              <label className="text-xs font-bold text-slate-700">
                Longitude
                <input
                  type="number"
                  step="any"
                  value={longitudeInput}
                  onChange={(e) => setLongitudeInput(e.target.value)}
                  placeholder="90.4125"
                  className="mt-1 block w-28 rounded-lg border border-slate-300 bg-white px-2 py-1.5 font-normal"
                  required
                />
              </label>
              <button
                type="submit"
                className="rounded-lg bg-blue-600 px-3 py-2 text-xs font-bold text-white hover:bg-blue-700"
              >
                অবস্থান দেখুন
              </button>
            </form>

            <button
              onClick={handleLocateMe}
              className="px-3.5 py-2 rounded-xl font-bold text-xs md:text-sm flex items-center gap-1.5 border bg-blue-50 border-blue-600 text-blue-800 hover:bg-blue-100 transition shadow-sm"
            >
              <Crosshair className="w-4 h-4" /> আমার জিপিএস লোকেশন
            </button>

            <button
              onClick={() => setMapType(mapType === "hybrid" ? "street" : "hybrid")}
              className="px-3.5 py-2 rounded-xl font-bold text-xs md:text-sm flex items-center gap-1.5 border bg-amber-50 border-amber-600 text-amber-900 hover:bg-amber-100 transition shadow-sm"
            >
              <Layers className="w-4 h-4" />
              {mapType === "hybrid" ? "স্ট্রিট ম্যাপ দেখুন" : "স্যাটেলাইট ম্যাপ দেখুন"}
            </button>

            <button
              onClick={() => setShowOverlay(!showOverlay)}
              className="px-3.5 py-2 rounded-xl font-bold text-xs md:text-sm flex items-center gap-1.5 border bg-emerald-50 border-emerald-600 text-emerald-800 hover:bg-emerald-100 transition shadow-sm"
            >
              <MapPin className="w-4 h-4" />
              {showOverlay ? "মৌজা দাগ লুকান" : "মৌজা দাগ দেখুন"}
            </button>
          </div>
          {coordinateError && (
            <div className="max-w-7xl mx-auto w-full px-4 pb-3 text-sm font-semibold text-red-600" role="alert">
              {coordinateError}
            </div>
          )}
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto w-full px-4 py-6 grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1">
        {/* Left Column: Dynamic Satellite Map */}
        <div className="lg:col-span-7 bg-white rounded-2xl shadow-md border border-slate-200 overflow-hidden flex flex-col">
          <div className="p-4 bg-slate-900 text-white flex flex-wrap justify-between items-center gap-2">
            <div>
              <h2 className="font-bold text-lg flex items-center gap-2">
                <MapPin className="w-5 h-5 text-emerald-400" />
                স্যাটেলাইট ম্যাপ ভিউ ({khatianInfo?.mouza || "মৌজা শনাক্ত হয়নি"})
              </h2>
              <p className="text-xs text-slate-300">
                ম্যাপের অবস্থান আলাদাভাবে নির্বাচন করতে হবে; OCR নিজে জমির GPS বা সীমানা নিশ্চিত করে না
              </p>
            </div>
            <div className="flex gap-3 text-xs font-bold bg-slate-800 px-3 py-1.5 rounded-lg border border-slate-700">
              <span className="flex items-center gap-1.5 text-emerald-300">
                <span className="w-3 h-3 rounded-full bg-emerald-500 inline-block"></span> নিরাপদ প্লট
              </span>
              <span className="flex items-center gap-1.5 text-red-300">
                <span className="w-3 h-3 rounded-full bg-red-500 inline-block"></span> বিরোধপূর্ণ প্লট
              </span>
            </div>
          </div>

          <div className="w-full relative z-0" style={{ height: "540px", minHeight: "540px" }}>
            <MapContainer
              center={mapCenter}
              zoom={mapZoom}
              scrollWheelZoom={true}
              style={{ height: "100%", width: "100%" }}
            >
              <MapController center={mapCenter} zoom={mapZoom} />
              <MapClickSelector onLocationSelect={handleMapLocationSelect} />

              {mapType === "hybrid" ? (
                <TileLayer
                  url="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}"
                  attribution="&copy; Google Satellite Hybrid"
                  maxZoom={20}
                />
              ) : (
                <TileLayer
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  attribution="&copy; OpenStreetMap contributors"
                  maxZoom={19}
                />
              )}

              {showOverlay && activeGeoData && (
                <GeoJSON
                  key={JSON.stringify(activeGeoData) + selectedDag + isCustomScan}
                  data={activeGeoData}
                  style={plotStyle}
                  onEachFeature={onEachPlot}
                />
              )}

              {isCustomScan && khatianInfo?.lat && khatianInfo?.lng && (
                <Marker position={[Number(khatianInfo.lat), Number(khatianInfo.lng)]}>
                  <Popup>
                    <strong>মৌজা: {khatianInfo.mouza}</strong>
                    <br />
                    খতিয়ান নং: {khatianInfo.khatian_no || "ছবিতে শনাক্ত হয়নি"}
                    <br />
                    দাগ নং: {khatianInfo.dag_no || "ছবিতে শনাক্ত হয়নি"}
                  </Popup>
                </Marker>
              )}

              {userGps && (
                <Marker position={userGps}>
                  <Popup>আপনার বর্তমান জিপিএস অবস্থান</Popup>
                </Marker>
              )}

              {selectedLocation && (
                <Marker position={selectedLocation}>
                  <Popup>
                    <strong>নির্বাচিত অবস্থান</strong>
                    <br />
                    Latitude: {selectedLocation[0].toFixed(7)}
                    <br />
                    Longitude: {selectedLocation[1].toFixed(7)}
                    <br />
                    <span>এই অবস্থান সরকারি জমির সীমানা হিসেবে যাচাই করা হয়নি।</span>
                  </Popup>
                </Marker>
              )}
            </MapContainer>
          </div>

          <div className="p-3 bg-slate-50 border-t text-xs text-slate-600 flex flex-wrap justify-between items-center gap-2">
            <span>
              <strong>ম্যাপের কেন্দ্রীয় কোঅর্ডিনেট:</strong> {mapCenter[0].toFixed(7)}, {mapCenter[1].toFixed(7)}
              {selectedLocation && (
                <span className="ml-2 text-blue-700 font-semibold">
                  নির্বাচিত: {selectedLocation[0].toFixed(7)}, {selectedLocation[1].toFixed(7)}
                </span>
              )}
            </span>
            <button
              onClick={() => {
                const coords = [23.6850, 90.3563];
                setMapCenter(coords);
                setMapZoom(7);
                setSelectedLocation(null);
                setUserGps(null);
                setLatitudeInput("");
                setLongitudeInput("");
                setCoordinateError("");
                setKhatianInfo(null);
                setSelectedDag(null);
                setIsCustomScan(false);
                setUploadedPreview(null);
                setActiveGeoData({ type: "FeatureCollection", features: [] });
              }}
              className="font-bold text-emerald-700 hover:underline flex items-center gap-1"
            >
              <RefreshCw className="w-3.5 h-3.5" /> ম্যাপ রিসেট করুন
            </button>
          </div>
        </div>

        {/* Right Column: AI Khatian Verification Report */}
        <div className="lg:col-span-5 flex flex-col gap-5">
          {loading ? (
            <div className="bg-white p-10 rounded-2xl shadow text-center border border-emerald-200 flex flex-col items-center justify-center gap-3 min-h-[340px]">
              <div className="w-12 h-12 border-4 border-emerald-600 border-t-transparent rounded-full animate-spin"></div>
              <p className="text-xl font-bold text-emerald-800 animate-pulse">
                এআই (AI) আপনার খতিয়ানের ছবিতে দৃশ্যমান তথ্য পড়ার চেষ্টা করছে...
              </p>
              <p className="text-xs text-slate-500">
                OCR ফলাফল সরকারি রেকর্ড বা জমির সীমানা যাচাই করে না।
              </p>
            </div>
          ) : !khatianInfo ? (
            <div className="bg-white p-8 rounded-2xl shadow-md border border-amber-300 min-h-[300px] flex flex-col justify-center gap-3">
              <div className="flex items-center gap-3 text-amber-800">
                <AlertTriangle className="w-8 h-8 shrink-0" />
                <h3 className="text-xl font-extrabold">সরকারি খতিয়ান ডেটাবেস সংযুক্ত নয়</h3>
              </div>
              <p className="text-sm leading-6 text-slate-700">
                খতিয়ানের ছবি আপলোড করলে দৃশ্যমান তথ্য OCR দিয়ে পড়ার চেষ্টা করা হবে। এই অ্যাপ এখনো সরকারি রেকর্ড, মালিকানা বা জমির সীমানা যাচাই করতে পারে না।
              </p>
              <p className="text-xs text-slate-500">ম্যাপে ক্লিক করে কোনো অবস্থান বেছে নিতে পারেন; সেটি সরকারি জমির সীমানা হিসেবে গণ্য হবে না।</p>
            </div>
          ) : (
            <>
              {isCustomScan && uploadedPreview && (
                <div className="bg-amber-50 border-2 border-amber-400 p-3.5 rounded-2xl flex items-center justify-between gap-4 shadow-sm">
                  <div className="flex items-center gap-3">
                    <img
                      src={uploadedPreview}
                      alt="Uploaded Khatian"
                      className="w-16 h-16 object-cover rounded-xl border border-amber-500 shadow-sm"
                    />
                    <div>
                      <span className="text-xs bg-amber-400 text-slate-950 font-extrabold px-2.5 py-0.5 rounded-full">
                        লাইভ এআই ওসিআর ও স্যাটেলাইট ট্র্যাকিং
                      </span>
                      <h4 className="font-extrabold text-sm text-slate-900 mt-1">
                        মৌজা: {khatianInfo.mouza || "ছবিতে শনাক্ত হয়নি"} {khatianInfo.jl_no ? `(জে.এল নং: ${khatianInfo.jl_no})` : ""}
                      </h4>
                    </div>
                  </div>
                </div>
              )}

              {/* Verification Status Card */}
              <div
                className={`p-5 rounded-2xl shadow-md border-2 ${
                  isSafe
                    ? "bg-emerald-50 border-emerald-500 text-emerald-950"
                    : "bg-red-50 border-red-500 text-red-950"
                }`}
              >
                <div className="flex items-start gap-4">
                  <div
                    className={`p-3.5 rounded-2xl text-white shadow-lg ${
                      isSafe ? "bg-emerald-600" : "bg-red-600 animate-pulse"
                    }`}
                  >
                    {isSafe ? <ShieldCheck className="w-9 h-9" /> : <AlertTriangle className="w-9 h-9" />}
                  </div>
                  <div className="flex-1">
                    <div className="flex justify-between items-center">
                      <span
                        className={`text-xs font-extrabold px-3 py-0.5 rounded-full ${
                          isSafe ? "bg-emerald-200 text-emerald-900" : "bg-red-200 text-red-900"
                        }`}
                      >
                        {isCustomScan ? "OCR স্ক্যান রিপোর্ট · সরকারি যাচাই হয়নি" : "রেকর্ড রিপোর্ট · সরকারি যাচাই হয়নি"}
                      </span>
                      <span className="text-xs font-bold">ঝুঁকি: {khatianInfo.risk_score ?? "মূল্যায়ন করা হয়নি"}</span>
                    </div>
                    <h3 className="text-xl md:text-2xl font-extrabold mt-1.5">{khatianInfo.status_bn}</h3>
                    <p className="text-sm mt-2 font-medium leading-relaxed bg-white/80 p-2.5 rounded-lg border border-black/5">
                      {khatianInfo.message_bn}
                    </p>
                  </div>
                </div>
              </div>

              {/* Land Health Card */}
              <div className="bg-white p-5 rounded-2xl shadow-md border border-slate-200">
                <div className="flex justify-between items-center border-b pb-2.5 mb-3.5">
                  <h4 className="font-extrabold text-lg flex items-center gap-2 text-slate-800">
                    <FileText className="w-5 h-5 text-emerald-600" /> জমির স্বাস্থ্য কার্ড (Land Health Card)
                  </h4>
                  <button
                    onClick={() => window.print()}
                    className="text-xs bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold px-3 py-1.5 rounded-lg flex items-center gap-1.5 border transition"
                  >
                    <Printer className="w-3.5 h-3.5" /> প্রিন্ট / PDF
                  </button>
                </div>

                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div className="col-span-2 bg-slate-50 p-3 rounded-xl border border-slate-200">
                    <p className="text-slate-500 text-xs font-medium">মৌজা ও অন্তর্ভুক্ত দাগ নম্বরসমূহ</p>
                    <p className="font-extrabold text-sm md:text-base text-slate-900 mt-0.5">
                      দাগ নং: {khatianInfo.dag_no || "ছবিতে শনাক্ত হয়নি"}
                    </p>
                    <p className="text-xs text-emerald-700 font-bold mt-0.5">
                      মৌজা: {khatianInfo.mouza || "ছবিতে শনাক্ত হয়নি"} {khatianInfo.jl_no ? `| জে.এল নং: ${khatianInfo.jl_no}` : ""}
                    </p>
                  </div>
                  <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
                    <p className="text-slate-500 text-xs font-medium">খতিয়ান নম্বর</p>
                    <p className="font-extrabold text-base text-slate-900 mt-0.5">
                      {khatianInfo.khatian_no || "ছবিতে শনাক্ত হয়নি"}
                    </p>
                  </div>
                  <div className="bg-emerald-50/60 p-3 rounded-xl border border-emerald-200">
                    <p className="text-emerald-800 text-xs font-semibold">সর্বমোট জমির পরিমাণ</p>
                    <p className="font-extrabold text-base text-emerald-700 mt-0.5">
                      {khatianInfo.total_area || "ছবিতে শনাক্ত হয়নি"}
                    </p>
                  </div>
                </div>

                <div className="mt-3.5 bg-slate-100 p-3 rounded-xl flex justify-between items-center border border-slate-200">
                  <span className="text-sm font-medium text-slate-600">
                    মালিকের নাম:{" "}
                    <strong className="text-slate-900 font-extrabold">
                      {khatianInfo.current_owner || "ছবিতে শনাক্ত হয়নি"}
                    </strong>
                  </span>
                  <span className="flex items-center gap-1 text-xs font-bold text-amber-700 shrink-0">
                    <AlertTriangle className="w-4 h-4" /> সরকারি যাচাই হয়নি
                  </span>
                </div>
              </div>

              {/* Plot-by-Plot Breakdown / Lineage Card */}
              {lineageList.length > 0 && (
                <div className="bg-white p-5 rounded-2xl shadow-md border border-slate-200">
                  <h4 className="font-extrabold text-lg border-b pb-2.5 mb-4 flex items-center gap-2 text-slate-800">
                    <GitBranch className="w-5 h-5 text-emerald-600" />
                    {isCustomScan ? "খতিয়ানের দাগভিত্তিক জমির বিবরণ" : "মালিকানার ধারাবাহিক ইতিহাস (Lineage)"}
                  </h4>
                  <div className="space-y-2.5 max-h-[280px] overflow-y-auto pr-1">
                    {lineageList.map((item, idx) => (
                      <div
                        key={idx}
                        className="p-3 rounded-xl border bg-slate-50 border-slate-200 flex justify-between items-center"
                      >
                        <div>
                          <span className="text-xs font-extrabold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800">
                            {item.stage}
                          </span>
                          <p className="font-bold text-sm text-slate-900 mt-1">{item.owner}</p>
                        </div>
                        <span className="text-sm font-extrabold px-3 py-1 rounded-lg border bg-white text-slate-800 border-slate-200 shrink-0">
                          {item.area}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </main>
    </div>
  );
}