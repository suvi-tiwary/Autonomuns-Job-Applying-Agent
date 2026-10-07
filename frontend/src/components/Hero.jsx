// src/components/Hero.jsx
import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import StruggleScene from "./StruggleScene";
import CTA from "./CTA";

export default function Hero({ onLaunchAgent }) {
  const [currentScene, setCurrentScene] = useState(0);

  // 2-page concise cinematic story flow: 1. The Struggle -> 2. The Solution & Launch
  const scenes = [
    { id: "story", label: "01. The Story", title: "The Job Search Struggle" },
    { id: "cta", label: "02. Launch Agent", title: "Autonomous Control" },
  ];

  const handleNext = () => {
    if (currentScene < scenes.length - 1) {
      setCurrentScene((prev) => prev + 1);
    } else {
      if (onLaunchAgent) onLaunchAgent();
    }
  };

  const handlePrev = () => {
    if (currentScene > 0) {
      setCurrentScene((prev) => prev - 1);
    }
  };

  // Keyboard navigation (Arrow keys & Spacebar)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "ArrowRight" || e.key === "ArrowDown") {
        if (currentScene < scenes.length - 1) {
          setCurrentScene((prev) => prev + 1);
        }
      } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
        if (currentScene > 0) {
          setCurrentScene((prev) => prev - 1);
        }
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [currentScene, scenes.length]);

  return (
    <div className="hero-cinematic-container">
      {/* Top Ambient Navigation Bar */}
      <header className="hero-cinematic-nav">
        <div className="hero-brand" onClick={() => setCurrentScene(0)} style={{ cursor: "pointer" }}>
          <div className="brand-orb">✦</div>
          <div className="brand-text">
            <h2>JobMate</h2>
            <span>Autonomous Career Engine</span>
          </div>
        </div>

        {/* 2-Scene Navigation Track */}
        <div className="hero-scene-nav-track">
          {scenes.map((scene, idx) => (
            <button
              key={scene.id}
              className={`scene-track-btn ${currentScene === idx ? "active" : ""}`}
              onClick={() => setCurrentScene(idx)}
            >
              <span className="track-index">{idx + 1}</span>
              <span className="track-label">{scene.label.split(". ")[1]}</span>
            </button>
          ))}
        </div>

        {/* GLOWING RED / WHITE GET STARTED BUTTON */}
        <div className="hero-header-action">
          <button
            className="glowing-red-white-btn header-btn"
            onClick={onLaunchAgent}
            title="Open the JobMate Dashboard"
          >
            <span className="btn-sparkle">✦</span>
            <span className="btn-text">Get Started</span>
            <span className="btn-arrow">→</span>
          </button>
        </div>
      </header>

      {/* Main Storyline Viewport (2 Slides) */}
      <main className="hero-viewport">
        <AnimatePresence mode="wait">
          {currentScene === 0 && (
            <motion.div
              key="scene-0"
              className="scene-slide-wrapper"
              initial={{ opacity: 0, scale: 0.96 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 1.04 }}
              transition={{ duration: 0.5, ease: "easeInOut" }}
            >
              <StruggleScene onNext={handleNext} onLaunch={onLaunchAgent} />
            </motion.div>
          )}

          {currentScene === 1 && (
            <motion.div
              key="scene-1"
              className="scene-slide-wrapper"
              initial={{ opacity: 0, scale: 0.96 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 1.04 }}
              transition={{ duration: 0.5, ease: "easeInOut" }}
            >
              <CTA onGetStarted={onLaunchAgent} />
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      {/* Bottom Floating Timeline Controls */}
      <footer className="hero-timeline-footer">
        <button
          className="timeline-arrow-btn"
          onClick={handlePrev}
          disabled={currentScene === 0}
          title="Previous Scene"
        >
          ← Prev
        </button>

        <div className="timeline-stepper">
          {scenes.map((scene, idx) => (
            <div
              key={scene.id}
              className={`timeline-dot ${currentScene === idx ? "active" : ""} ${currentScene > idx ? "completed" : ""}`}
              onClick={() => setCurrentScene(idx)}
              title={scene.title}
            >
              <span className="dot-inner" />
            </div>
          ))}
        </div>

        <button
          className="timeline-arrow-btn next"
          onClick={handleNext}
          title={currentScene === scenes.length - 1 ? "Open Dashboard" : "Next Scene"}
        >
          {currentScene === scenes.length - 1 ? "Launch Dashboard →" : "Next: Launch Control →"}
        </button>
      </footer>
    </div>
  );
}
