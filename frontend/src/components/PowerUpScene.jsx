// src/components/PowerUpScene.jsx
import React from "react";
import { motion } from "framer-motion";

export default function PowerUpScene({ onNext }) {
  const achievements = [
    { title: "Interview Request", company: "Anthropic AI", role: "AI Systems Engineer", time: "Just now", icon: "🔥", badge: "Direct Invite" },
    { title: "ATS Match Score", score: "98%", role: "Senior Backend (Python/Go)", time: "Auto-Scored", icon: "⚡", badge: "Top 1%" },
    { title: "Browser Auto-Filled", company: "Stripe", role: "Platform Engineer", time: "2 min ago", icon: "✓", badge: "Verified ATS" },
  ];

  return (
    <div className="scene-container powerup-scene">
      {/* Golden / Purple Energy Burst Background */}
      <div className="powerup-ambient-glow" />
      <div className="energy-grid-lines" />

      <div className="powerup-visual-center">
        {/* Glowing Aura & Transformed Developer Station */}
        <div className="powerup-character-station">
          <div className="aura-ring aura-outer" />
          <div className="aura-ring aura-middle" />
          <div className="aura-ring aura-inner" />

          <svg viewBox="0 0 400 320" className="powerup-svg" fill="none" xmlns="http://www.w3.org/2000/svg">
            {/* Ambient Base Glow */}
            <ellipse cx="200" cy="280" rx="190" ry="30" fill="url(#goldenGlow)" filter="blur(16px)" />

            {/* Futuristic Standing Desk */}
            <rect x="40" y="210" width="320" height="10" rx="5" fill="#1e1836" stroke="#a55eea" strokeWidth="2" />
            <rect x="60" y="220" width="8" height="65" fill="#2d2150" />
            <rect x="332" y="220" width="8" height="65" fill="#2d2150" />

            {/* Glowing Ultra-Wide Curved Monitor */}
            <path d="M70 145 C150 135, 250 135, 330 145 L320 205 C250 197, 150 197, 80 205 Z" fill="#0d0a1c" stroke="#fed330" strokeWidth="2.5" />
            <path d="M78 149 C150 141, 250 141, 322 149 L314 201 C250 195, 150 195, 86 201 Z" fill="url(#screenGoldenPulse)" />

            {/* Developer (Upright, Confident, Empowered) */}
            {/* Torso */}
            <path d="M168 190 Q200 130 232 190 L220 230 L180 230 Z" fill="#4b3ca7" stroke="#a55eea" strokeWidth="1.5" />
            
            {/* Head looking up at glowing offers */}
            <circle cx="200" cy="115" r="22" fill="#574b90" stroke="#fed330" strokeWidth="2" />
            
            {/* Glowing Crown / Neural Headset */}
            <path d="M182 108 Q200 95 218 108" stroke="#fed330" strokeWidth="3" strokeLinecap="round" />
            <circle cx="200" cy="98" r="4" fill="#fed330" />

            {/* Arms typing dynamically on holographic keyboard */}
            <path d="M175 160 Q150 185 140 210" stroke="#786fa6" strokeWidth="7" strokeLinecap="round" />
            <path d="M225 160 Q250 185 260 210" stroke="#786fa6" strokeWidth="7" strokeLinecap="round" />

            {/* Holographic Keyboard */}
            <rect x="130" y="208" width="140" height="6" rx="3" fill="#fed330" opacity="0.8" filter="blur(1px)" />

            {/* Gradients */}
            <defs>
              <radialGradient id="goldenGlow" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="#fed330" stopOpacity="0.45" />
                <stop offset="60%" stopColor="#8854d0" stopOpacity="0.2" />
                <stop offset="100%" stopColor="#000000" stopOpacity="0" />
              </radialGradient>
              <linearGradient id="screenGoldenPulse" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#a55eea" stopOpacity="0.4" />
                <stop offset="50%" stopColor="#fed330" stopOpacity="0.3" />
                <stop offset="100%" stopColor="#20bf6b" stopOpacity="0.4" />
              </linearGradient>
            </defs>
          </svg>
        </div>

        {/* Floating Success Notifications & Opportunity Cards */}
        <div className="powerup-cards-float">
          {achievements.map((item, idx) => (
            <motion.div
              key={idx}
              className="achievement-card"
              initial={{ opacity: 0, y: 30, scale: 0.85 }}
              animate={{
                opacity: 1,
                y: [0, -8, 0],
                scale: 1,
              }}
              transition={{
                duration: 4,
                repeat: Infinity,
                ease: "easeInOut",
                delay: idx * 0.4,
              }}
            >
              <div className="ach-icon">{item.icon}</div>
              <div className="ach-details">
                <div className="ach-top">
                  <strong>{item.title}</strong>
                  <span className="ach-badge">{item.badge}</span>
                </div>
                <div className="ach-sub">
                  <span>{item.company || item.score}</span>
                  <small>&bull; {item.role || item.time}</small>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Cinematic Text Overlay */}
      <motion.div
        className="scene-text-card"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.2 }}
      >
        <div className="scene-step-tag gold-tag">
          <span className="dot pulse-gold" /> SCENE 03 &bull; POWER-UP TRANSFORMATION
        </div>
        <h2 className="scene-title">
          From cold rejections to <span className="highlight-gold">opportunities finding you.</span>
        </h2>
        <p className="scene-subtitle">
          Your resume is active across live job pipelines. High-relevance interviews start booking on your placement radar while you focus on building.
        </p>

        {onNext && (
          <button className="scene-next-btn gold-btn" onClick={onNext}>
            <span>Watch Jobs Rain Down</span>
            <span className="arrow-icon">↓</span>
          </button>
        )}
      </motion.div>
    </div>
  );
}
