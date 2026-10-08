// src/components/AgentSettingsBar.jsx
import React, { useState, useEffect } from "react";
import { getAgentSettings, saveAgentSettings } from "../services/api";

export default function AgentSettingsBar({ onSettingsChanged }) {
  const [settings, setSettings] = useState({
    auto_answer_descriptive: true,
    auto_submit: false,
    preferred_model: "openai/gpt-oss-120b",
    max_answer_words: 150,
  });
  const [saving, setSaving] = useState(false);
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    async function loadSettings() {
      try {
        const s = await getAgentSettings();
        if (s) {
          setSettings(s);
          if (onSettingsChanged) onSettingsChanged(s);
        }
      } catch (err) {
        console.warn("Could not load agent settings:", err);
      }
    }
    loadSettings();
  }, []);

  const handleToggleAutoAnswer = async () => {
    const updated = {
      ...settings,
      auto_answer_descriptive: !settings.auto_answer_descriptive,
    };
    setSettings(updated);
    if (onSettingsChanged) onSettingsChanged(updated);
    try {
      await saveAgentSettings(updated);
    } catch (e) {
      console.error(e);
    }
  };

  const handleToggleAutoSubmit = async () => {
    const updated = {
      ...settings,
      auto_submit: !settings.auto_submit,
    };
    setSettings(updated);
    if (onSettingsChanged) onSettingsChanged(updated);
    try {
      await saveAgentSettings(updated);
    } catch (e) {
      console.error(e);
    }
  };

  const handleSaveAll = async () => {
    setSaving(true);
    try {
      await saveAgentSettings(settings);
      if (onSettingsChanged) onSettingsChanged(settings);
      setShowModal(false);
    } catch (e) {
      console.error(e);
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      {/* Quick Agent Safety Control Pills */}
      <div className="agent-controls-bar">
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span style={{ fontSize: "14px" }}>🤖</span>
          <span style={{ fontSize: "12px", fontWeight: "600", color: "#a5b4fc" }}>
            AGENT SAFETY CONTROLS
          </span>
        </div>

        <div className="agent-toggle-pill" onClick={handleToggleAutoAnswer} title="Click to toggle LLM descriptive question generator">
          <span className={`toggle-indicator ${settings.auto_answer_descriptive ? "on" : "off"}`} />
          <span>Auto-Answer Descriptive Questions:</span>
          <strong style={{ color: settings.auto_answer_descriptive ? "#4ade80" : "#f87171" }}>
            {settings.auto_answer_descriptive ? "ON" : "OFF"}
          </strong>
        </div>

        <div className="agent-toggle-pill" onClick={handleToggleAutoSubmit} title="Click to toggle auto-submit (Default is OFF for manual applicant review)">
          <span className={`toggle-indicator ${settings.auto_submit ? "on" : "off"}`} />
          <span>Auto-Submit:</span>
          <strong style={{ color: settings.auto_submit ? "#4ade80" : "#fbbf24" }}>
            {settings.auto_submit ? "ON" : "OFF (Ready for Review)"}
          </strong>
        </div>

        <button
          className="btn-settings-gear"
          onClick={() => setShowModal(true)}
          title="Configure detailed LLM agent parameters"
        >
          ⚙ Settings
        </button>
      </div>

      {/* Settings Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <h3 style={{ margin: 0, color: "#fff", display: "flex", alignItems: "center", gap: "8px" }}>
                <span>⚙</span> Autonomous Agent Configuration
              </h3>
              <button
                onClick={() => setShowModal(false)}
                style={{ background: "transparent", border: "none", color: "#9ca3af", fontSize: "20px", cursor: "pointer" }}
              >
                ×
              </button>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              <div className="setting-toggle-row">
                <div>
                  <strong style={{ color: "#fff", display: "block", fontSize: "14px" }}>
                    Intelligent Descriptive Answer Generator (LLM)
                  </strong>
                  <small style={{ color: "#9ca3af" }}>
                    Automatically detects open-ended questions ("Why this company?", "Explain a project", "Cover letter") and crafts tailored truthful answers.
                  </small>
                </div>
                <input
                  type="checkbox"
                  checked={settings.auto_answer_descriptive}
                  onChange={handleToggleAutoAnswer}
                  style={{ width: "20px", height: "20px", accentColor: "#8d6bff" }}
                />
              </div>

              <div className="setting-toggle-row">
                <div>
                  <strong style={{ color: "#fff", display: "block", fontSize: "14px" }}>
                    Auto-Submit Applications
                  </strong>
                  <small style={{ color: "#9ca3af" }}>
                    When OFF, Playwright fills every verified field and pauses visibly at READY_FOR_REVIEW for your final click.
                  </small>
                </div>
                <input
                  type="checkbox"
                  checked={settings.auto_submit}
                  onChange={handleToggleAutoSubmit}
                  style={{ width: "20px", height: "20px", accentColor: "#8d6bff" }}
                />
              </div>

              <div className="profile-input-group">
                <label>Maximum Words per Descriptive Answer</label>
                <input
                  type="number"
                  min="50"
                  max="500"
                  value={settings.max_answer_words || 150}
                  onChange={(e) =>
                    setSettings({ ...settings, max_answer_words: parseInt(e.target.value) || 150 })
                  }
                />
              </div>

              <div className="profile-input-group">
                <label>LLM Model Engine</label>
                <select
                  value={settings.preferred_model || "openai/gpt-oss-120b"}
                  onChange={(e) => setSettings({ ...settings, preferred_model: e.target.value })}
                >
                  <option value="openai/gpt-oss-120b">openai/gpt-oss-120b (Primary High-Precision)</option>
                  <option value="llama-3.3-70b-versatile">llama-3.3-70b-versatile</option>
                  <option value="llama-3.1-8b-instant">llama-3.1-8b-instant (Fastest)</option>
                </select>
              </div>

              <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "12px" }}>
                <button onClick={() => setShowModal(false)} className="btn-outline">
                  Close
                </button>
                <button onClick={handleSaveAll} disabled={saving} className="btn-primary-glow">
                  {saving ? "Saving..." : "Save Settings"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
