// src/components/JobRainCard.jsx
import React from "react";
import { motion } from "framer-motion";

export default function JobRainCard({ job, style, onClick, isFeatured = false }) {
  const {
    title,
    company,
    location,
    salary,
    match,
    logo,
    color = "#8d6bff",
    tags = [],
  } = job;

  return (
    <motion.div
      className={`job-rain-card ${isFeatured ? "featured" : ""}`}
      style={{
        ...style,
        "--card-color": color,
      }}
      whileHover={{
        scale: 1.08,
        rotateZ: 0,
        zIndex: 50,
        boxShadow: `0 20px 40px rgba(0, 0, 0, 0.8), 0 0 30px ${color}40`,
      }}
      transition={{ type: "spring", stiffness: 300, damping: 20 }}
      onClick={onClick}
    >
      <div className="rain-card-glow" style={{ background: `radial-gradient(circle at 50% 0%, ${color}33, transparent 70%)` }} />
      
      <div className="rain-card-header">
        <div className="rain-company-badge" style={{ borderColor: `${color}60`, background: `${color}15` }}>
          <span className="rain-company-logo">{logo || company.charAt(0)}</span>
          <span className="rain-company-name">{company}</span>
        </div>
        <div className="rain-match-pill" style={{ background: `${color}20`, borderColor: `${color}80`, color }}>
          <span className="sparkle">✦</span> {match}% Match
        </div>
      </div>

      <h4 className="rain-job-title">{title}</h4>

      <div className="rain-job-meta">
        <span className="meta-item">📍 {location}</span>
        {salary && <span className="meta-item salary">💰 {salary}</span>}
      </div>

      {tags && tags.length > 0 && (
        <div className="rain-tags">
          {tags.slice(0, 2).map((t, idx) => (
            <span key={idx} className="rain-tag">
              {t}
            </span>
          ))}
        </div>
      )}

      <div className="rain-card-footer">
        <span className="rain-status">⚡ Verified ATS</span>
        <button className="rain-apply-btn" style={{ background: `linear-gradient(135deg, ${color}, #6240ff)` }}>
          Apply with AI →
        </button>
      </div>
    </motion.div>
  );
}
