// src/components/StruggleScene.jsx
import React from "react";
import { motion } from "framer-motion";

export default function StruggleScene({ onNext, onLaunch }) {
  const rejections = [
    { text: "Application Rejected", delay: 0.2, x: "-26%", y: "10%", rotate: -6, color: "#ff4757" },
    { text: "No Response (3 weeks)", delay: 0.6, x: "28%", y: "8%", rotate: 8, color: "#ff6b81" },
    { text: "0 Interviews", delay: 1.0, x: "-30%", y: "42%", rotate: 4, color: "#ffa502" },
    { text: "Ghosted after Round 3", delay: 1.4, x: "30%", y: "45%", rotate: -5, color: "#ff4757" },
    { text: "Searching: 450+ Jobs...", delay: 1.8, x: "0%", y: "55%", rotate: 0, color: "#747d8c" },
  ];

  return (
    <div className="scene-container struggle-scene">
      {/* Background ambient lighting */}
      <div className="struggle-ambient-darkness" />

      {/* Floating Rejection Badges */}
      <div className="floating-rejections-layer">
        {rejections.map((item, idx) => (
          <motion.div
            key={idx}
            className="rejection-pill"
            style={{
              left: `calc(50% + ${item.x})`,
              top: item.y,
              borderColor: `${item.color}40`,
              color: item.color,
              boxShadow: `0 0 25px ${item.color}20`,
            }}
            initial={{ opacity: 0, scale: 0.7, y: 30, rotate: item.rotate }}
            animate={{
              opacity: [0.6, 0.9, 0.6],
              scale: [0.95, 1.02, 0.95],
              y: [0, -10, 0],
            }}
            transition={{
              opacity: { duration: 3, repeat: Infinity, ease: "easeInOut", delay: item.delay },
              scale: { duration: 4, repeat: Infinity, ease: "easeInOut", delay: item.delay },
              y: { duration: 3.5, repeat: Infinity, ease: "easeInOut", delay: item.delay },
            }}
          >
            <span className="pill-cross">✕</span>
            <span>{item.text}</span>
          </motion.div>
        ))}
      </div>

      {/* 1. PERSON / DEVELOPER IMAGE ON TOP */}
      <div className="struggle-visual-center" style={{ marginBottom: "16px", marginTop: "10px" }}>
        <div className="desk-lamp-glow" />

        <div className="developer-silhouette-card">
          <svg viewBox="0 0 400 270" className="struggle-svg" fill="none" xmlns="http://www.w3.org/2000/svg">
            {/* Dark room shadows */}
            <ellipse cx="200" cy="245" rx="180" ry="25" fill="rgba(0,0,0,0.85)" filter="blur(12px)" />

            {/* Desk */}
            <rect x="50" y="195" width="300" height="12" rx="4" fill="#181822" stroke="#2a2a38" strokeWidth="2" />
            <rect x="70" y="207" width="10" height="50" fill="#12121a" />
            <rect x="320" y="207" width="10" height="50" fill="#12121a" />

            {/* Developer Figure (Hunched, Exhausted) */}
            {/* Chair */}
            <rect x="180" y="145" width="40" height="60" rx="6" fill="#1a1a24" />
            <rect x="195" y="205" width="10" height="40" fill="#121218" />

            {/* Body */}
            <path d="M165 185 Q190 120 220 170 Q235 195 235 200 L165 200 Z" fill="#252535" />

            {/* Head bent down over laptop */}
            <circle cx="185" cy="110" r="22" fill="#2e2e42" />
            <path d="M175 115 Q160 135 150 155" stroke="#2e2e42" strokeWidth="12" strokeLinecap="round" />

            {/* Arm resting on desk holding head */}
            <path d="M190 130 Q165 155 155 190" stroke="#3b3b54" strokeWidth="8" strokeLinecap="round" />

            {/* Laptop with dim blue/red glare */}
            <polygon points="120,193 170,193 165,150 125,150" fill="#0d0d14" stroke="#4a4a60" strokeWidth="1.5" />
            {/* Screen Glare */}
            <polygon points="126,153 164,153 168,189 122,189" fill="url(#screenGlare)" />
            {/* Screen glow reflection on face */}
            <circle cx="180" cy="117" r="14" fill="url(#faceGlow)" opacity="0.35" />

            {/* Coffee mugs */}
            <rect x="255" y="180" width="14" height="15" rx="2" fill="#303042" stroke="#45455c" />
            <circle cx="285" cy="191" r="6" fill="#20202c" />
            <circle cx="95" cy="192" r="5" fill="#20202c" />

            {/* Gradients */}
            <defs>
              <linearGradient id="screenGlare" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#ff4757" stopOpacity="0.45" />
                <stop offset="100%" stopColor="#371217" stopOpacity="0.05" />
              </linearGradient>
              <radialGradient id="faceGlow" cx="40%" cy="60%" r="60%">
                <stop offset="0%" stopColor="#ff6b81" stopOpacity="0.7" />
                <stop offset="100%" stopColor="#ff6b81" stopOpacity="0" />
              </radialGradient>
            </defs>
          </svg>
        </div>
      </div>

      {/* 2. TEXT & CALL-TO-ACTIONS IN THE DOWN / BOTTOM */}
      <div className="struggle-text-content" style={{ position: "relative", zIndex: 10 }}>
        {/* Scene Tag */}
        <div className="scene-step-tag struggle-tag">
          <span className="dot pulse-red" /> SCENE 01 &bull; THE STRUGGLE
        </div>

        <h1 className="scene-title">
          Applying to jobs shouldn't feel like a <span className="highlight-red">full-time job.</span>
        </h1>

        <p className="scene-subtitle">
          Endless cold forms, ghosting, and generic ATS filters drain your energy. Watch your autonomous AI agent take over the entire application pipeline in foreground.
        </p>

        {/* Action Buttons */}
        <div className="scene-action-row" style={{ marginTop: "18px", display: "flex", gap: "14px", flexWrap: "wrap", justifyContent: "center" }}>
          {onLaunch && (
            <button
              className="glowing-red-white-btn"
              onClick={onLaunch}
              title="Launch Dashboard Directly"
            >
              <span className="btn-sparkle">✦</span>
              <span className="btn-text">Launch Your AI Agent</span>
              <span className="btn-arrow">→</span>
            </button>
          )}

          {onNext && (
            <button className="scene-next-btn red-btn" onClick={onNext}>
              <span>Discover the Solution</span>
              <span className="arrow-icon">→</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
