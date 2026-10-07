// src/components/CTA.jsx
import React from "react";
import { motion } from "framer-motion";

export default function CTA({ onGetStarted }) {
  return (
    <div className="scene-container hero-cta-scene">
      {/* Background Lighting & Glow Effects */}
      <div className="cta-ambient-glow" />
      <div className="cta-radial-sweep" />

      <motion.div
        className="cta-card-central"
        initial={{ opacity: 0, scale: 0.9, y: 30 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
      >
        {/* Status Indicator Pill */}
        <div className="agent-status-badge">
          <span className="pulsing-beacon" />
          <span className="beacon-text">✦ AI Agent Ready & Autonomous Engine Online</span>
        </div>

        {/* Hero Title */}
        <h1 className="cta-headline">
          Stop Searching Manually. <br />
          <span className="cta-gradient-text">Let Your AI Agent Apply In Foreground.</span>
        </h1>

        <p className="cta-description">
          Upload your resume, pinpoint real direct ATS job postings, and watch the visible Chromium browser open right on your screen to fill applications automatically.
        </p>

        {/* Feature Badges */}
        <div className="cta-feature-pills">
          <div className="feature-pill">
            <span className="f-icon">🌐</span>
            <span>Real Chromium Foreground Browser</span>
          </div>
          <div className="feature-pill">
            <span className="f-icon">🎯</span>
            <span>100% Direct Verified ATS Postings</span>
          </div>
          <div className="feature-pill">
            <span className="f-icon">📄</span>
            <span>Instant PDF Resume Parsing</span>
          </div>
          <div className="feature-pill">
            <span className="f-icon">🛡️</span>
            <span>Human-In-The-Loop Safety Review</span>
          </div>
        </div>

        {/* THE GLOWING WHITE & RED CALL-TO-ACTION BUTTON */}
        <div className="cta-button-container">
          <button
            id="launch-agent-cta-btn"
            className="glowing-red-white-btn"
            onClick={onGetStarted}
            title="Get Started and open JobMate Dashboard"
          >
            <span className="btn-glow-layer" />
            <span className="btn-sparkle">✦</span>
            <span className="btn-text">Get Started &bull; Launch Your AI Agent</span>
            <span className="btn-arrow">→</span>
          </button>
        </div>

        <div className="cta-guarantee-note">
          <span>⚡ No manual form typing required &bull; 1-click workspace launch &bull; Ready for deployment</span>
        </div>
      </motion.div>
    </div>
  );
}
