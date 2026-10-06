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
          <div>
            <h3>{title}</h3>
            <p>{company}</p>
          </div>
          {match && (
            <div className="match">
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
          {job.salary && <span>₹ {job.salary}</span>}
          {job.job_type && <span>{job.job_type}</span>}
        </div>
        {job.description && (
          <p className="job-description">
            {job.description.length > 180 ? `${job.description.slice(0, 180)}...` : job.description}
          </p>
        )}
        <div className="job-actions">
          {url !== "#" && (
            <a href={url} target="_blank" rel="noreferrer" className="view-job">
              View job 
            </a>
          )}
          <button className="apply-button" onClick={onApply}>
            Apply with AI <span>→</span>
          </button>
        </div>
      </div>
    </div>
  );
}