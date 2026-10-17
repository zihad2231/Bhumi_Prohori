
import { useState } from "react";
import {
  MapContainer,
  TileLayer,
  CircleMarker,
  Popup,
  useMapEvents,
  useMap,
} from "react-leaflet";
import "leaflet/dist/leaflet.css";

function MapClickHandler({ onSelect }) {
  useMapEvents({
    click(event) {
      onSelect(event.latlng.lat, event.latlng.lng);
    },
  });

  return null;
}

function MapUpdater({ position }) {
  const map = useMap();

  if (position) {
    map.setView(position, 17);
  }

  return null;
}

export default function LandLocationPicker({ onLocationSelect }) {
  const [latitude, setLatitude] = useState("");
  const [longitude, setLongitude] = useState("");
  const [position, setPosition] = useState(null);
  const [error, setError] = useState("");

  function selectLocation(lat, lng) {
    setLatitude(lat.toFixed(7));
    setLongitude(lng.toFixed(7));
    setPosition([lat, lng]);
    setError("");

    onLocationSelect?.({
      latitude: lat,
      longitude: lng,
    });
  }

  function findCoordinates(event) {
    event.preventDefault();

    const lat = Number(latitude);
    const lng = Number(longitude);

    if (
      latitude.trim() === "" ||
      longitude.trim() === "" ||
      !Number.isFinite(lat) ||
      !Number.isFinite(lng) ||
      lat < -90 ||
      lat > 90 ||
      lng < -180 ||
      lng > 180
    ) {
      setError("সঠিক Latitude ও Longitude দিন।");
      return;
    }

    selectLocation(lat, lng);
  }

  return (
    <section className="land-location-picker">
      <h2>জমির অবস্থান নির্বাচন করুন</h2>
      <p>স্যাটেলাইট ম্যাপে জমির অবস্থানে ক্লিক করুন অথবা GPS Coordinates দিন।</p>

      <form onSubmit={findCoordinates} className="coordinates-form">
        <label>
          Latitude
          <input
            type="number"
            step="any"
            value={latitude}
            onChange={(e) => setLatitude(e.target.value)}
            placeholder="যেমন: 23.8103"
            required
          />
        </label>

        <label>
          Longitude
          <input
            type="number"
            step="any"
            value={longitude}
            onChange={(e) => setLongitude(e.target.value)}
            placeholder="যেমন: 90.4125"
            required
          />
        </label>

        <button type="submit">অবস্থান দেখুন</button>
      </form>

      {error && <p role="alert">{error}</p>}

      <div style={{ height: "450px", width: "100%", marginTop: "16px" }}>
        <MapContainer
          center={[23.8103, 90.4125]}
          zoom={7}
          style={{ height: "100%", width: "100%" }}
        >
          <TileLayer
            attribution='Imagery © <a href="https://www.esri.com/">Esri</a>'
            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
          />

          <MapClickHandler onSelect={selectLocation} />
          <MapUpdater position={position} />

          {position && (
            <CircleMarker
              center={position}
              radius={9}
              pathOptions={{
                color: "#ffffff",
                fillColor: "#e53935",
                fillOpacity: 0.9,
                weight: 3,
              }}
            >
              <Popup>
                <strong>নির্বাচিত অবস্থান</strong>
                <br />
                Latitude: {latitude}
                <br />
                Longitude: {longitude}
              </Popup>
            </CircleMarker>
          )}
        </MapContainer>
      </div>

      {position && (
        <p>
          নির্বাচিত অবস্থান: {latitude}, {longitude}
        </p>
      )}
    </section>
  );
}
