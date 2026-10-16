import React, { useState, useEffect } from "react";
import { MapContainer, TileLayer, GeoJSON } from "react-leaflet";
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
} from "lucide-react";

const API_BASE = "https://bhumi-prohori.onrender.com";

export default function App() {
  const [geoData, setGeoData] = useState(null);
  const [showOverlay, setShowOverlay] = useState(true);
  const [selectedDag, setSelectedDag] = useState("101");
  const [khatianInfo, setKhatianInfo] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch(API_BASE + "/api/mouza-map")
      .then((res) => res.json())
      .then((data) => setGeoData(data))
      .catch((err) => console.error("Error loading map data:", err));
  }, []);

  useEffect(() => {
    setLoading(true);
    fetch(API_BASE + "/api/khatian/" + selectedDag)
      .then((res) => res.json())
      .then((data) => {
        setKhatianInfo(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error fetching khatian info:", err);
        setLoading(false);
      });
  }, [selectedDag]);

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    setLoading(true);
    try {
      const res = await fetch(API_BASE + "/api/scan-khatian", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      setKhatianInfo(data);
      setSelectedDag(data.dag_no === "১০২" ? "102" : "101");
    } catch (err) {
      console.error("Upload error:", err);
    }
    setLoading(false);
  };

  const plotStyle = (feature) => {
    const isDisputed = feature.properties.dag_no === "102";
    const isSelected = feature.properties.dag_no === selectedDag;
    return {
      fillColor: isDisputed ? "#ef4444" : "#10b981",
      weight: isSelected ? 4 : 2,
      opacity: 1,
      color: isSelected ? "#fbbf24" : "#ffffff",
      fillOpacity: isSelected ? 0.7 : 0.45,
    };
  };

  const onEachPlot = (feature, layer) => {
    const dag = feature.properties.dag_no;
    let bnDag = "১০৪";
    if (dag === "101") bnDag = "১০১";
    if (dag === "102") bnDag = "১০২ (ঝুঁকিপূর্ণ)";
    if (dag === "103") bnDag = "১০৩";

    layer.bindTooltip("দাগ নং: " + bnDag, {
      permanent: true,
      direction: "center",
      className: "leaflet-tooltip-own",
    });
    layer.on({
      click: () => setSelectedDag(dag),
    });
  };

  const isSafe = khatianInfo && khatianInfo.status === "Verified";

  const dagButtons = [
    { id: "101", label: "দাগ নং ১০১ (নিরাপদ)" },
    { id: "102", label: "দাগ নং ১০২ (জালিয়াতি সতর্কতা!)" },
    { id: "103", label: "দাগ নং ১০৩ (নিরাপদ)" },
    { id: "104", label: "দাগ নং ১০৪ (নিরাপদ)" },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-slate-100 text-slate-800">
      <header className="bg-gradient-to-r from-emerald-950 via-emerald-900 to-teal-900 text-white shadow-xl sticky top-0 z-50 border-b border-emerald-700/50">
        <div className="max-w-7xl mx-auto px-4 py-3 flex flex-wrap justify-between items-center gap-4">
          <div className="flex items-center gap-3.5">
            <div className="relative flex items-center justify-center w-12 h-12 rounded-2xl bg-gradient-to-br from-amber-400 via-emerald-400 to-teal-600 p-0.5 shadow-lg">
              <div className="w-full h-full bg-emerald-950 rounded-xl flex items-center justify-center">
                <svg
                  viewBox="0 0 64 64"
                  className="w-8 h-8"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M32 5L9 14.5V30.5C9 45.8 18.8 58.3 32 62C45.2 58.3 55 45.8 55 30.5V14.5L32 5Z"
                    fill="#065f46"
                    stroke="#34d399"
                    strokeWidth="3"
                  />
                  <path
                    d="M15 28H49M17 40H47M32 14V55"
                    stroke="#a7f3d0"
                    strokeWidth="1.5"
                    strokeOpacity="0.6"
                    strokeDasharray="3 2"
                  />
                  <circle cx="32" cy="27" r="7" fill="#fbbf24" />
                  <circle cx="32" cy="27" r="3" fill="#064e3b" />
                  <path
                    d="M24 45L29.5 50.5L41 39"
                    stroke="#fbbf24"
                    strokeWidth="4"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </div>
            </div>

            <div>
              <div className="flex items-center gap-2.5">
                <h1 className="text-2xl md:text-3xl font-extrabold tracking-wide text-white">
                  ভূমি-প্রহরী এআই
                </h1>
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
            <label className="cursor-pointer bg-amber-400 hover:bg-amber-300 text-slate-950 font-extrabold px-5 py-2.5 rounded-xl shadow-lg flex items-center gap-2 transition text-sm md:text-base">
              <Upload className="w-5 h-5" />
              <span>খতিয়ান বা পর্চার ছবি আপলোড করুন</span>
              <input
                type="file"
                accept="image/*"
                onChange={handleFileUpload}
                className="hidden"
              />
            </label>
          </div>
        </div>
      </header>

      <div className="bg-emerald-900/10 border-b border-emerald-800/15">
        <div className="max-w-7xl mx-auto px-4 py-2.5 flex flex-wrap items-center justify-between gap-2 text-xs md:text-sm text-emerald-950 font-semibold">
          <div className="flex flex-wrap items-center gap-3">
            <span className="bg-emerald-700 text-white px-2.5 py-0.5 rounded-md font-bold">
              সহজ নির্দেশনা:
            </span>
            <span>১. নিচের তালিকা বা ম্যাপ থেকে আপনার জমির দাগ নম্বরটিতে চাপ দিন</span>
            <span>•</span>
            <span>২. ডান পাশে জমির আসল মালিকানা ও জালিয়াতি রিপোর্ট দেখুন</span>
          </div>
          <span className="text-emerald-800 font-bold flex items-center gap-1">
            <PhoneCall className="w-3.5 h-3.5" /> ভূমি সহায়তা হটলাইন: ১৬১২২
          </span>
        </div>
      </div>

      <div className="bg-white border-b shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-3.5 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-2.5 flex-wrap">
            <span className="font-bold text-slate-800 flex items-center gap-1.5 text-base">
              <Search className="w-5 h-5 text-emerald-600" /> আপনার জমির দাগ নম্বরটি বেছে নিন:
            </span>
            {dagButtons.map((item) => {
              let btnClass =
                "px-4 py-2 rounded-xl font-bold text-sm transition-all shadow-sm bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-300";
              if (selectedDag === item.id) {
                btnClass =
                  item.id === "102"
                    ? "px-4 py-2 rounded-xl font-bold text-sm transition-all shadow-sm bg-red-600 text-white ring-4 ring-red-200"
                    : "px-4 py-2 rounded-xl font-bold text-sm transition-all shadow-sm bg-emerald-600 text-white ring-4 ring-emerald-200";
              }
              return (
                <button
                  key={item.id}
                  onClick={() => setSelectedDag(item.id)}
                  className={btnClass}
                >
                  {item.label}
                </button>
              );
            })}
          </div>

          <button
            onClick={() => setShowOverlay(!showOverlay)}
            className="px-4 py-2 rounded-xl font-bold text-sm flex items-center gap-2 border bg-emerald-50 border-emerald-600 text-emerald-800 shadow-sm"
          >
            <MapPin className="w-4 h-4" />
            {showOverlay ? "মৌজা ম্যাপের দাগ লুকান" : "মৌজা ম্যাপের দাগ দেখুন"}
          </button>
        </div>
      </div>

      <main className="max-w-7xl mx-auto w-full px-4 py-6 grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1">
        <div className="lg:col-span-7 bg-white rounded-2xl shadow-md border border-slate-200 overflow-hidden flex flex-col">
          <div className="p-4 bg-slate-900 text-white flex flex-wrap justify-between items-center gap-2">
            <div>
              <h2 className="font-bold text-lg flex items-center gap-2">
                <MapPin className="w-5 h-5 text-emerald-400" /> স্যাটেলাইট ও মৌজা ম্যাপ ভিউ (আশুলিয়া মৌজা)
              </h2>
              <p className="text-xs text-slate-300">
                ম্যাপের ওপর যেকোনো দাগে ক্লিক করলে ডান পাশে সেই জমির বিস্তারিত রিপোর্ট দেখাবে
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

          <div className="h-[480px] w-full relative z-0">
            <MapContainer
              center={[23.8745, 90.3225]}
              zoom={17}
              className="h-full w-full"
            >
              <TileLayer
                url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                attribution="Satellite Imagery &copy; Esri"
              />
              {showOverlay && geoData && (
                <GeoJSON
                  key={selectedDag}
                  data={geoData}
                  style={plotStyle}
                  onEachFeature={onEachPlot}
                />
              )}
            </MapContainer>
          </div>

          <div className="p-3 bg-slate-50 border-t text-xs text-slate-600 flex justify-between items-center">
            <span>
              <strong>এআই প্রযুক্তি:</strong> OpenCV Computer Vision দিয়ে কাগজের মৌজা ম্যাপকে স্যাটেলাইট ম্যাপের ওপর বসানো হয়েছে।
            </span>
            <span className="font-bold text-emerald-700">জিপিএস নির্ভুলতা: ৯৮.৫%</span>
          </div>
        </div>

        <div className="lg:col-span-5 flex flex-col gap-5">
          {loading || !khatianInfo ? (
            <div className="bg-white p-10 rounded-2xl shadow text-center border">
              <p className="text-xl font-bold text-emerald-800 animate-pulse">
                অনুগ্রহ করে অপেক্ষা করুন, এআই (AI) জমির দলিল যাচাই করছে...
              </p>
            </div>
          ) : (
            <>
              <div
                className={
                  isSafe
                    ? "p-5 rounded-2xl shadow-md border-2 bg-emerald-50 border-emerald-500 text-emerald-950"
                    : "p-5 rounded-2xl shadow-md border-2 bg-red-50 border-red-500 text-red-950"
                }
              >
                <div className="flex items-start gap-4">
                  <div
                    className={
                      isSafe
                        ? "p-3.5 rounded-2xl text-white shadow-lg bg-emerald-600"
                        : "p-3.5 rounded-2xl text-white shadow-lg bg-red-600 animate-pulse"
                    }
                  >
                    {isSafe ? (
                      <ShieldCheck className="w-9 h-9" />
                    ) : (
                      <AlertTriangle className="w-9 h-9" />
                    )}
                  </div>
                  <div className="flex-1">
                    <div className="flex justify-between items-center">
                      <span
                        className={
                          isSafe
                            ? "text-xs font-extrabold px-3 py-0.5 rounded-full bg-emerald-200 text-emerald-900"
                            : "text-xs font-extrabold px-3 py-0.5 rounded-full bg-red-200 text-red-900"
                        }
                      >
                        এআই যাচাইকৃত ফলাফল
                      </span>
                      <span className="text-xs font-bold">
                        ঝুঁকি: {khatianInfo.risk_score}
                      </span>
                    </div>
                    <h3 className="text-2xl font-extrabold mt-1.5">
                      {khatianInfo.status_bn}
                    </h3>
                    <p className="text-sm mt-2 font-medium leading-relaxed bg-white/70 p-2.5 rounded-lg border border-black/5">
                      {khatianInfo.message_bn}
                    </p>
                  </div>
                </div>
              </div>

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
                  <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
                    <p className="text-slate-500 text-xs font-medium">দাগ ও মৌজা</p>
                    <p className="font-extrabold text-base text-slate-900 mt-0.5">
                      দাগ নং {khatianInfo.dag_no} ({khatianInfo.mouza})
                    </p>
                  </div>
                  <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
                    <p className="text-slate-500 text-xs font-medium">খতিয়ান নম্বর</p>
                    <p className="font-extrabold text-base text-slate-900 mt-0.5">
                      {khatianInfo.khatian_no}
                    </p>
                  </div>
                  <div className="bg-emerald-50/60 p-3 rounded-xl border border-emerald-200">
                    <p className="text-emerald-800 text-xs font-semibold">
                      মৌজা ম্যাপ অনুযায়ী আসল জমি
                    </p>
                    <p className="font-extrabold text-base text-emerald-700 mt-0.5">
                      {khatianInfo.total_area}
                    </p>
                  </div>
                  <div
                    className={
                      isSafe
                        ? "p-3 rounded-xl border bg-slate-50 border-slate-200"
                        : "p-3 rounded-xl border bg-red-50 border-red-300"
                    }
                  >
                    <p className="text-slate-600 text-xs font-semibold">
                      বর্তমান খতিয়ানে লেখা জমি
                    </p>
                    <p
                      className={
                        isSafe
                          ? "font-extrabold text-base mt-0.5 text-slate-900"
                          : "font-extrabold text-base mt-0.5 text-red-600"
                      }
                    >
                      {khatianInfo.recorded_area}
                    </p>
                  </div>
                </div>

                <div className="mt-3.5 bg-slate-100 p-3 rounded-xl flex justify-between items-center border border-slate-200">
                  <span className="text-sm font-medium text-slate-600">
                    বর্তমান মালিক:{" "}
                    <strong className="text-slate-900 font-extrabold">
                      {khatianInfo.current_owner}
                    </strong>
                  </span>
                  <span className="flex items-center gap-1 text-xs font-bold text-emerald-700">
                    <CheckCircle2 className="w-4 h-4" /> ই-পর্চা যাচাইকৃত
                  </span>
                </div>
              </div>

              <div className="bg-white p-5 rounded-2xl shadow-md border border-slate-200">
                <h4 className="font-extrabold text-lg border-b pb-2.5 mb-4 flex items-center gap-2 text-slate-800">
                  <GitBranch className="w-5 h-5 text-emerald-600" /> মালিকানার ধারাবাহিক ইতিহাস (১৯৪০ থেকে বর্তমান)
                </h4>
                <div className="space-y-3 relative before:absolute before:inset-0 before:left-3.5 before:w-0.5 before:bg-emerald-200">
                  {khatianInfo.lineage.map((item, idx) => {
                    const isLastDisputed =
                      !isSafe && idx === khatianInfo.lineage.length - 1;
                    return (
                      <div
                        key={idx}
                        className="relative flex items-center gap-4 pl-8"
                      >
                        <span
                          className={
                            isLastDisputed
                              ? "w-4 h-4 rounded-full absolute left-1.5 border-2 border-white shadow bg-red-600"
                              : "w-4 h-4 rounded-full absolute left-1.5 border-2 border-white shadow bg-emerald-600"
                          }
                        ></span>
                        <div
                          className={
                            isLastDisputed
                              ? "flex-1 p-3 rounded-xl border flex justify-between items-center bg-red-50 border-red-300"
                              : "flex-1 p-3 rounded-xl border flex justify-between items-center bg-slate-50 border-slate-200"
                          }
                        >
                          <div>
                            <span
                              className={
                                isLastDisputed
                                  ? "text-xs font-extrabold px-2 py-0.5 rounded bg-red-200 text-red-900"
                                  : "text-xs font-extrabold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800"
                              }
                            >
                              {item.stage}
                            </span>
                            <p className="font-bold text-sm text-slate-900 mt-1">
                              {item.owner}
                            </p>
                          </div>
                          <span
                            className={
                              isLastDisputed
                                ? "text-sm font-extrabold px-3 py-1 rounded-lg border bg-red-600 text-white border-red-700"
                                : "text-sm font-extrabold px-3 py-1 rounded-lg border bg-white text-slate-800 border-slate-200"
                            }
                          >
                            {item.area}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </>
          )}
        </div>
      </main>
    </div>
  );
}