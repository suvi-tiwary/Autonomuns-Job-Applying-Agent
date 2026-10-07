// src/components/JobCard.jsx
import React from "react";

export default function JobCard({ job, onApply }) {
  const title = job.title || "Software Engineer";
  const company = job.company || "Company";
  const location = job.location || "Remote";
  const remoteType = job.remote_type || "Remote";
  const url = job.apply_url || job.job_url || job.url || "#";
  const match = job.match_score || null;
  const ats = job.ats || (job.source ? job.source.split(" ")[0] : "ATS");
  const isVerified = job.is_verified !== false;

  return (
    <div className="job-card">
      <div className="company-logo">{company.charAt(0).toUpperCase()}</div>
      <div className="job-main">
        <div className="job-top">
          <div style={{ minWidth: 0, flex: 1, marginRight: "12px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap", marginBottom: "4px" }}>
              <h3 style={{ wordBreak: "break-word", overflowWrap: "break-word", margin: 0 }}>{title}</h3>
              {isVerified && (
                <span
                  style={{
                    fontSize: "11px",
                    background: "rgba(46, 213, 115, 0.12)",
                    color: "#2ed573",
                    border: "1px solid rgba(46, 213, 115, 0.3)",
                    padding: "2px 7px",
                    borderRadius: "12px",
                    fontWeight: "600",
                  }}
                >
                  ✓ Verified Post
                </span>
              )}
            </div>
            <p style={{ wordBreak: "break-word", overflowWrap: "break-word", margin: "2px 0 0", color: "#a0a0b0" }}>{company}</p>
          </div>
          {match && (
            <div className="match" style={{ flexShrink: 0 }}>
              <strong>
                {typeof match === "number"
                  ? `${Math.round(match > 1 ? match : match * 100)}%`
                  : match}
              </strong>
              <small>match</small>
            </div>
          )}
        </div>

        <div className="job-meta">
          <span>⌖ {location}</span>
          <span>🏢 {remoteType}</span>
          <span style={{ textTransform: "capitalize" }}>📌 {ats}</span>
          {job.salary && <span>💰 {job.salary}</span>}
        </div>

        {job.description && (
          <p
            className="job-description"
            style={{
              wordBreak: "break-word",
              overflowWrap: "break-word",
              lineHeight: "1.6",
            }}
          >
            {job.description.length > 200 ? `${job.description.slice(0, 200)}...` : job.description}
          </p>
        )}

        {/* Extracted Requirements pills if present */}
        {job.requirements && job.requirements.length > 0 && (
          <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", margin: "8px 0" }}>
            {job.requirements.slice(0, 2).map((req, idx) => (
              <span
                key={idx}
                style={{
                  fontSize: "11px",
                  background: "rgba(255, 255, 255, 0.04)",
                  border: "1px solid rgba(255, 255, 255, 0.08)",
                  color: "#8e8e9e",
                  padding: "3px 8px",
                  borderRadius: "6px",
                  maxWidth: "100%",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap"
                }}
              >
                • {req}
              </span>
            ))}
          </div>
        )}

        <div className="job-actions">
          {url !== "#" && (
            <a
              href={url}
              target="_blank"
              rel="noreferrer"
              className="view-job"
              style={{
                textDecoration: "none",
                display: "inline-flex",
                alignItems: "center",
                gap: "4px",
              }}
            >
              View Job ↗
            </a>
          )}
          <button className="apply-button" onClick={onApply}>
            <span>✦</span> Apply with AI <span>→</span>
          </button>
        </div>
      </div>
    </div>
  );
}