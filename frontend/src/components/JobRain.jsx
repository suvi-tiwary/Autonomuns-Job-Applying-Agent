// src/components/JobRain.jsx
import React, { useState } from "react";
import { motion } from "framer-motion";
import JobRainCard from "./JobRainCard";

export default function JobRain({ onNext, onSelectJob }) {
  const [selectedFilter, setSelectedFilter] = useState("All");

  const rainJobs = [
    {
      id: "rain-1",
      title: "Senior AI / ML Engineer",
      company: "Anthropic",
      location: "San Francisco, CA / Remote",
      salary: "$195,000 - $260,000",
      match: 99,
      logo: "🔮",
      color: "#d97706",
      tags: ["Python", "PyTorch", "LLM Agents"],
    },
    {
      id: "rain-2",
      title: "Staff Autonomous Agent Developer",
      company: "OpenAI",
      location: "Remote (Global)",
      salary: "$210,000 - $290,000",
      match: 98,
      logo: "❇️",
      color: "#10b981",
      tags: ["FastAPI", "Playwright", "Tool Use"],
    },
    {
      id: "rain-3",
      title: "Lead Full Stack Engineer",
      company: "Stripe",
      location: "Seattle, WA / Remote",
      salary: "$180,000 - $240,000",
      match: 96,
      logo: "💳",
      color: "#6366f1",
      tags: ["React", "TypeScript", "Node.js"],
    },
    {
      id: "rain-4",
      title: "Founding AI Engineer",
      company: "Perplexity AI",
      location: "San Francisco / Remote",
      salary: "$190,000 - $250,000",
      match: 97,
      logo: "🪐",
      color: "#06b6d4",
      tags: ["RAG Systems", "Search Indexing"],
    },
    {
      id: "rain-5",
      title: "Senior Backend Infrastructure",
      company: "Databricks",
      location: "Remote / Hybrid",
      salary: "$185,000 - $245,000",
      match: 95,
      logo: "🧱",
      color: "#ef4444",
      tags: ["Distributed Systems", "Go", "Python"],
    },
    {
      id: "rain-6",
      title: "AI Product Engineer",
      company: "Linear",
      location: "Remote (Global)",
      salary: "$165,000 - $220,000",
      match: 98,
      logo: "⚡",
      color: "#8b5cf6",
      tags: ["GraphQL", "React 19", "AI Workflows"],
    },
  ];

  return (
    <div className="scene-container job-rain-scene">
      {/* Dynamic Background */}
      <div className="rain-ambient-glow" />
      <div className="rain-matrix-particles" />

      {/* Floating Header Banner */}
      <div className="rain-scene-header">
        <div className="scene-step-tag blue-tag">
          <span className="dot pulse-blue" /> SCENE 04 &bull; LIVE JOB STREAMS
        </div>
        <h2 className="scene-title">
          Opportunities <span className="highlight-blue">pouring in</span> in real time.
        </h2>
        <p className="scene-subtitle">
          Every posting is pre-verified directly against live company ATS platforms (Greenhouse, Lever, Ashby, Workable). No 404s, no generic portals.
        </p>

        {/* Live Counters */}
        <div className="rain-stats-bar">
          <div className="rain-stat-item">
            <span className="stat-num">12,480+</span>
            <span className="stat-lbl">Active Verified ATS Jobs</span>
          </div>
          <div className="rain-stat-divider" />
          <div className="rain-stat-item">
            <span className="stat-num">98.4%</span>
            <span className="stat-lbl">Precision Semantic Match</span>
          </div>
          <div className="rain-stat-divider" />
          <div className="rain-stat-item">
            <span className="stat-num">0s</span>
            <span className="stat-lbl">Manual Form Typing</span>
          </div>
        </div>
      </div>

      {/* 3D Falling / Cascading Job Rain Grid */}
      <div className="rain-cards-viewport">
        <div className="rain-column col-1">
          {rainJobs.slice(0, 3).map((job, idx) => (
            <JobRainCard
              key={job.id}
              job={job}
              onClick={() => onSelectJob && onSelectJob(job)}
              style={{
                animationDelay: `${idx * 0.3}s`,
              }}
            />
          ))}
        </div>

        <div className="rain-column col-2 offset">
          {rainJobs.slice(3, 6).map((job, idx) => (
            <JobRainCard
              key={job.id}
              job={job}
              onClick={() => onSelectJob && onSelectJob(job)}
              style={{
                animationDelay: `${idx * 0.4 + 0.2}s`,
              }}
            />
          ))}
        </div>
      </div>

      {/* Scene Next Trigger */}
      {onNext && (
        <div className="rain-bottom-cta">
          <button className="scene-next-btn blue-btn" onClick={onNext}>
            <span>Take Autonomous Command</span>
            <span className="arrow-icon">↓</span>
          </button>
        </div>
      )}
    </div>
  );
}
