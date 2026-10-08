// src/components/ApplicationDetailModal.jsx
import React, { useState, useEffect } from "react";
import { getApplicationFields } from "../services/api";

export default function ApplicationDetailModal({ application, onClose }) {
  const [fields, setFields] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadFields() {
      if (!application?.id) return;
      setLoading(true);
      try {
        const data = await getApplicationFields(application.id);
        setFields(data || []);
      } catch (err) {
        console.error("Failed to load application fields:", err);
      } finally {
        setLoading(false);
      }
    }
    loadFields();
  }, [application]);

  if (!application) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" style={{ maxWidth: "720px", width: "95%" }} onClick={(e) => e.stopPropagation()}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px" }}>
          <div>
            <h3 style={{ margin: "0 0 4px 0", color: "#fff" }}>
              {application.job_title || "Application Session"}
            </h3>
            <span style={{ fontSize: "13px", color: "#a5b4fc" }}>
              🏢 {application.company || "Company"} &bull; 🕒 {application.timestamp}
            </span>
          </div>
          <button
            onClick={onClose}
            style={{ background: "transparent", border: "none", color: "#9ca3af", fontSize: "22px", cursor: "pointer" }}
          >
            ×
          </button>
        </div>

        {/* Application Metadata Badges */}
        <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginBottom: "16px" }}>
          <span className="badge-source">Status: {application.status}</span>
          {application.apply_url && (
            <a
              href={application.apply_url}
              target="_blank"
              rel="noreferrer"
              style={{ fontSize: "12px", color: "#818cf8", textDecoration: "none", padding: "4px 8px", background: "rgba(99, 102, 241, 0.1)", borderRadius: "6px" }}
            >
              Open Job Link ↗
            </a>
          )}
        </div>

        <h4 style={{ margin: "16px 0 8px 0", color: "#fff", fontSize: "14px", borderBottom: "1px solid rgba(255,255,255,0.08)", paddingBottom: "6px" }}>
          Automated Field Inspection & Decision Trace ({fields.length} events)
        </h4>

        {loading ? (
          <div style={{ padding: "20px", textAlign: "center", color: "#9ca3af" }}>
            <span className="spinner"></span> Loading field decision logs...
          </div>
        ) : fields.length === 0 ? (
          <div className="empty-substate">
            <p>No detailed field events recorded for this session yet.</p>
          </div>
        ) : (
          <div style={{ maxHeight: "380px", overflowY: "auto", display: "flex", flexDirection: "column", gap: "10px", paddingRight: "4px" }}>
            {fields.map((f, idx) => (
              <div key={idx} className="field-log-row">
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "8px", marginBottom: "4px" }}>
                  <strong style={{ color: "#fff", fontSize: "13px" }}>
                    {f.question || f.field_name || "Field"}
                  </strong>
                  <span
                    className={`badge-field-source source-${(f.source || "PROFILE").toLowerCase()}`}
                  >
                    {f.source}
                  </span>
                </div>

                <div style={{ fontSize: "12px", color: "#9ca3af", marginBottom: "4px" }}>
                  Type: <span style={{ color: "#c7d2fe" }}>{f.detected_type}</span>
                </div>

                {f.generated_answer && (
                  <div style={{ background: "rgba(0,0,0,0.3)", padding: "8px 10px", borderRadius: "6px", fontSize: "12px", color: "#d1d5db", borderLeft: "2px solid #8d6bff" }}>
                    {f.generated_answer}
                  </div>
                )}

                {f.error && (
                  <div style={{ color: "#fbbf24", fontSize: "12px", marginTop: "4px" }}>
                    ⚠ {f.error}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "16px" }}>
          <button onClick={onClose} className="btn-primary-glow">
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
