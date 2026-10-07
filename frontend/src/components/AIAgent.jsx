// src/components/AIAgent.jsx
import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";

export default function AIAgent({ onNext }) {
  const [activeScanIndex, setActiveScanIndex] = useState(0);

  const scanItems = [
    { label: "Parsing Resume Structure", detail: "Extracting skills, projects & achievements", icon: "📄", progress: "100%" },
    { label: "Indexing Core Skills", detail: "Python, FastAPI, Machine Learning, React", icon: "⚡", progress: "100%" },
    { label: "Calculating Experience Level", detail: "Hands-on Fullstack & AI Agent Development", icon: "🏆", progress: "100%" },
    { label: "Filtering Target Roles", detail: "AI/ML Engineer, Backend Developer, SWE", icon: "🎯", progress: "Active" },
    { label: "Matching Geographies", detail: "Remote, India, Europe & Global Tier-1 Tech", icon: "🌐", progress: "Optimized" },
  ];

  useEffect(() => {
    const timer = setInterval(() => {
      setActiveScanIndex((prev) => (prev + 1) % scanItems.length);
    }, 2200);
    return () => clearInterval(timer);
  }, [scanItems.length]);

  return (
    <div className="scene-container ai-agent-scene">
      {/* Cyan/Purple Energy Background */}
      <div className="ai-agent-ambient-glow" />

      {/* Center Holographic Entity & Laser Scanner */}
      <div className="ai-agent-visual-center">
        {/* Holographic Glowing Orb with Particles */}
        <div className="hologram-orb-wrapper">
          <div className="orb-core">
            <div className="orb-inner-sphere" />
            <div className="orb-ring ring-1" />
            <div className="orb-ring ring-2" />
            <div className="orb-ring ring-3" />
            <div className="orb-laser-scanner" />
          </div>

          <div className="ai-entity-title-tag">
            <span className="pulse-cyan-dot" />
            <strong>JobMate Autonomous Agent</strong>
            <small>Neural Engine Active</small>
          </div>
        </div>

        {/* Live Holographic Data Matrix / Scanning Stream */}
        <div className="scanner-matrix-panel">
          <div className="matrix-header">
            <span className="matrix-status">⚡ AUTONOMOUS RESUME & PROFILE SCANNER</span>
            <span className="matrix-id">SYS-ID: AGY-9000</span>
          </div>

          <div className="scan-items-list">
            {scanItems.map((item, idx) => {
              const isActive = idx === activeScanIndex;
              return (
                <motion.div
                  key={idx}
                  className={`scan-item-row ${isActive ? "active" : ""}`}
                  initial={{ opacity: 0.5, x: -10 }}
                  animate={{
                    opacity: isActive ? 1 : 0.65,
                    x: isActive ? 6 : 0,
                    scale: isActive ? 1.02 : 1,
                  }}
                  transition={{ duration: 0.3 }}
                >
                  <div className="scan-icon-col">{item.icon}</div>
                  <div className="scan-info-col">
                    <div className="scan-label-row">
                      <strong>{item.label}</strong>
                      <span className="scan-badge">{item.progress}</span>
                    </div>
                    <small>{item.detail}</small>
                  </div>
                  {isActive && <div className="scan-laser-indicator" />}
                </motion.div>
              );
            })}
          </div>

          <div className="matrix-footer">
            <div className="live-stream-code">
              <span>&gt; scanning DOM structures...</span>
              <span>&gt; mapping profile tokens...</span>
              <span>&gt; ready for autonomous matching.</span>
            </div>
          </div>
        </div>
      </div>

      {/* Cinematic Text Overlay */}
      <motion.div
        className="scene-text-card"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.3 }}
      >
        <div className="scene-step-tag ai-tag">
          <span className="dot pulse-cyan" /> SCENE 02 &bull; THE AI ARRIVAL
        </div>
        <h2 className="scene-title">
          What if you had an <span className="highlight-cyan">AI agent</span> working for you?
        </h2>
        <p className="scene-subtitle">
          An autonomous partner that digests your background, pinpoints matching roles with high semantic accuracy, and prepares your applications 24/7.
        </p>

        {onNext && (
          <button className="scene-next-btn cyan-btn" onClick={onNext}>
            <span>Witness the Transformation</span>
            <span className="arrow-icon">↓</span>
          </button>
        )}
      </motion.div>
    </div>
  );
}
