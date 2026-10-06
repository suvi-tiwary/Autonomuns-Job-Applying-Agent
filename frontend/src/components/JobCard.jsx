// src/components/JobCard.jsx
import React from "react";

export default function JobCard({ job, onApply }) {
  const title = job.title || job.job_title || job.position || "Software Engineer";
  const company = job.company || job.company_name || "Company";
  const location = job.location || job.job_location || "Remote";
  const url = job.url || job.link || job.job_url || "#";
  const match = job.match_score || job.similarity || job.score || null;

  return (
    <div className="job-card">
      <div className="company-logo">{company.charAt(0).toUpperCase()}</div>
      <div className="job-main">
        <div className="job-top">
          <div style={{ minWidth: 0, flex: 1, marginRight: "12px" }}>
            <h3 style={{ wordBreak: "break-word", overflowWrap: "break-word" }}>{title}</h3>
            <p style={{ wordBreak: "break-word", overflowWrap: "break-word" }}>{company}</p>
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
          {job.salary && <span>💰 {job.salary}</span>}
          {job.job_type && <span>💼 {job.job_type}</span>}
          {job.source && <span>📌 {job.source}</span>}
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
            {job.description.length > 220 ? `${job.description.slice(0, 220)}...` : job.description}
          </p>
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
              Direct Post ↗
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