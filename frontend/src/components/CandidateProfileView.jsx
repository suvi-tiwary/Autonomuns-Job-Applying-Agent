// src/components/CandidateProfileView.jsx
import React, { useState, useEffect } from "react";
import { saveCandidateProfile } from "../services/api";

export default function CandidateProfileView({
  initialProfile,
  resumeName,
  resumePath,
  onProfileUpdated,
  onUploadNewResume,
}) {
  const [profile, setProfile] = useState(initialProfile || {});
  const [activeTab, setActiveTab] = useState("personal");
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState("");

  // New item draft states
  const [newSkill, setNewSkill] = useState("");
  const [newAchievement, setNewAchievement] = useState("");
  const [newCertification, setNewCertification] = useState("");
  const [newRole, setNewRole] = useState("");
  const [newLocation, setNewLocation] = useState("");
  const [newCustomKey, setNewCustomKey] = useState("");
  const [newCustomVal, setNewCustomVal] = useState("");

  // Draft project
  const [showAddProject, setShowAddProject] = useState(false);
  const [projectDraft, setProjectDraft] = useState({
    name: "",
    description: "",
    technologies: "",
    url: "",
  });

  // Draft experience
  const [showAddExp, setShowAddExp] = useState(false);
  const [expDraft, setExpDraft] = useState({
    company: "",
    role: "",
    duration: "",
    description: "",
  });

  useEffect(() => {
    if (initialProfile) {
      setProfile(initialProfile);
    }
  }, [initialProfile]);

  const extractedSet = new Set(profile.extracted_fields || []);

  const isExtracted = (fieldKey) => extractedSet.has(fieldKey);

  // Field updater helpers
  const updateNested = (section, field, value) => {
    setProfile((prev) => ({
      ...prev,
      [section]: {
        ...(prev[section] || {}),
        [field]: value,
      },
    }));
    setSaveSuccess(false);
  };

  const handleSave = async () => {
    setSaving(true);
    setSaveError("");
    try {
      const res = await saveCandidateProfile(profile);
      if (res && res.profile) {
        setProfile(res.profile);
        if (onProfileUpdated) {
          onProfileUpdated(res.profile);
        }
      }
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 4000);
    } catch (err) {
      console.error("Save profile error:", err);
      setSaveError(err.message || "Failed to save profile.");
    } finally {
      setSaving(false);
    }
  };

  // Skill management
  const addSkill = () => {
    if (!newSkill.trim()) return;
    const current = profile.professional?.key_skills || [];
    if (!current.includes(newSkill.trim())) {
      updateNested("professional", "key_skills", [...current, newSkill.trim()]);
    }
    setNewSkill("");
  };

  const removeSkill = (skillToRemove) => {
    const current = profile.professional?.key_skills || [];
    updateNested(
      "professional",
      "key_skills",
      current.filter((s) => s !== skillToRemove)
    );
  };

  // Project management
  const handleAddProject = () => {
    if (!projectDraft.name.trim()) return;
    const techList = projectDraft.technologies
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean);
    const newProj = {
      name: projectDraft.name.trim(),
      title: projectDraft.name.trim(),
      description: projectDraft.description.trim(),
      technologies: techList,
      url: projectDraft.url.trim(),
    };
    const current = profile.professional?.projects || [];
    updateNested("professional", "projects", [...current, newProj]);
    setProjectDraft({ name: "", description: "", technologies: "", url: "" });
    setShowAddProject(false);
  };

  const removeProject = (index) => {
    const current = profile.professional?.projects || [];
    updateNested(
      "professional",
      "projects",
      current.filter((_, i) => i !== index)
    );
  };

  // Experience management
  const handleAddExperience = () => {
    if (!expDraft.company.trim()) return;
    const newExp = {
      company: expDraft.company.trim(),
      role: expDraft.role.trim() || "Intern / Engineer",
      duration: expDraft.duration.trim(),
      description: expDraft.description.trim(),
    };
    const current = profile.professional?.experience || [];
    updateNested("professional", "experience", [...current, newExp]);
    setExpDraft({ company: "", role: "", duration: "", description: "" });
    setShowAddExp(false);
  };

  const removeExperience = (index) => {
    const current = profile.professional?.experience || [];
    updateNested(
      "professional",
      "experience",
      current.filter((_, i) => i !== index)
    );
  };

  // Custom fields
  const addCustomField = () => {
    if (!newCustomKey.trim()) return;
    const current = profile.custom_fields || {};
    setProfile((prev) => ({
      ...prev,
      custom_fields: {
        ...current,
        [newCustomKey.trim()]: newCustomVal.trim(),
      },
    }));
    setNewCustomKey("");
    setNewCustomVal("");
    setSaveSuccess(false);
  };

  const removeCustomField = (keyToRemove) => {
    const current = { ...(profile.custom_fields || {}) };
    delete current[keyToRemove];
    setProfile((prev) => ({
      ...prev,
      custom_fields: current,
    }));
    setSaveSuccess(false);
  };

  const p = profile.personal || {};
  const e = profile.education || {};
  const l = profile.links || {};
  const prof = profile.professional || {};
  const pref = profile.preferences || {};
  const custom = profile.custom_fields || {};

  return (
    <div className="candidate-profile-container">
      {/* HEADER BAR */}
      <div className="profile-header-card">
        <div style={{ display: "flex", alignItems: "center", gap: "16px", flex: 1, minWidth: 0 }}>
          <div className="profile-avatar">
            {p.full_name ? p.full_name.charAt(0).toUpperCase() : "👤"}
          </div>
          <div style={{ minWidth: 0, flex: 1 }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
              <h3 style={{ margin: 0, fontSize: "20px", color: "#fff" }}>
                {p.full_name || "Persistent Candidate Profile"}
              </h3>
              <span className="profile-source-badge">
                ⚡ Source of Truth for Auto-Apply
              </span>
            </div>
            <p style={{ margin: "4px 0 0 0", fontSize: "13px", color: "#9ca3af" }}>
              {resumeName ? `Resume: ${resumeName}` : "No resume file attached"}
              {p.email && ` • ${p.email}`}
              {p.phone && ` • ${p.phone}`}
            </p>
          </div>
        </div>

        <div style={{ display: "flex", gap: "10px", alignItems: "center", flexWrap: "wrap" }}>
          {onUploadNewResume && (
            <button
              onClick={onUploadNewResume}
              className="btn-outline"
              title="Upload a new PDF resume to extract and update fields"
            >
              📄 Upload New Resume
            </button>
          )}

          <button
            onClick={handleSave}
            disabled={saving}
            className="btn-primary-glow"
          >
            {saving ? (
              <>
                <span className="spinner"></span> Saving...
              </>
            ) : saveSuccess ? (
              "✓ Saved in Database"
            ) : (
              "Save Profile Changes"
            )}
          </button>
        </div>
      </div>

      {saveSuccess && (
        <div className="success-banner">
          ✨ Candidate Profile successfully saved to database. All future applications will reuse these verified details!
        </div>
      )}

      {saveError && (
        <div className="error-box">
          ⚠ {saveError}
        </div>
      )}

      {/* TABS NAVIGATION */}
      <div className="profile-tabs-bar">
        {[
          { id: "personal", label: "Personal", icon: "👤" },
          { id: "education", label: "Education", icon: "🎓" },
          { id: "links", label: "Links & Socials", icon: "🔗" },
          { id: "professional", label: `Professional & Skills (${prof.key_skills?.length || 0})`, icon: "💼" },
          { id: "projects", label: `Projects (${prof.projects?.length || 0})`, icon: "🚀" },
          { id: "experience", label: `Experience (${prof.experience?.length || 0})`, icon: "🏢" },
          { id: "preferences", label: "Preferences & Work Auth", icon: "🎯" },
          { id: "custom", label: `Custom Fields (${Object.keys(custom).length})`, icon: "🧩" },
        ].map((tab) => (
          <button
            key={tab.id}
            className={`profile-tab-btn ${activeTab === tab.id ? "active" : ""}`}
            onClick={() => setActiveTab(tab.id)}
          >
            <span>{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>

      {/* TAB CONTENT */}
      <div className="profile-tab-content">
        {/* ================= PERSONAL TAB ================= */}
        {activeTab === "personal" && (
          <div className="form-grid-2">
            <div className="profile-input-group">
              <div className="label-row">
                <label>Full Name</label>
                {isExtracted("personal.full_name") && (
                  <span className="badge-extracted">Extracted</span>
                )}
              </div>
              <input
                type="text"
                value={p.full_name || ""}
                onChange={(e) => updateNested("personal", "full_name", e.target.value)}
                placeholder="e.g. Suvi Tiwary"
              />
            </div>

            <div className="profile-input-group">
              <div className="label-row">
                <label>Email Address</label>
                {isExtracted("personal.email") && (
                  <span className="badge-extracted">Extracted</span>
                )}
              </div>
              <input
                type="email"
                value={p.email || ""}
                onChange={(e) => updateNested("personal", "email", e.target.value)}
                placeholder="candidate@example.com"
              />
            </div>

            <div className="profile-input-group">
              <div className="label-row">
                <label>Phone Number</label>
                {isExtracted("personal.phone") && (
                  <span className="badge-extracted">Extracted</span>
                )}
              </div>
              <input
                type="tel"
                value={p.phone || ""}
                onChange={(e) => updateNested("personal", "phone", e.target.value)}
                placeholder="+1 555-0199 or +91 9876543210"
              />
            </div>

            <div className="profile-input-group">
              <div className="label-row">
                <label>Current Location / City</label>
                {isExtracted("personal.location") && (
                  <span className="badge-extracted">Extracted</span>
                )}
              </div>
              <input
                type="text"
                value={p.location || ""}
                onChange={(e) => updateNested("personal", "location", e.target.value)}
                placeholder="Bengaluru, India / San Francisco, CA"
              />
            </div>

            <div className="profile-input-group">
              <div className="label-row">
                <label>City</label>
                {isExtracted("personal.city") && (
                  <span className="badge-extracted">Extracted</span>
                )}
              </div>
              <input
                type="text"
                value={p.city || ""}
                onChange={(e) => updateNested("personal", "city", e.target.value)}
                placeholder="Bengaluru"
              />
            </div>

            <div className="profile-input-group">
              <div className="label-row">
                <label>State / Province</label>
                {isExtracted("personal.state") && (
                  <span className="badge-extracted">Extracted</span>
                )}
              </div>
              <input
                type="text"
                value={p.state || ""}
                onChange={(e) => updateNested("personal", "state", e.target.value)}
                placeholder="Karnataka / California"
              />
            </div>

            <div className="profile-input-group">
              <div className="label-row">
                <label>Country</label>
                {isExtracted("personal.country") && (
                  <span className="badge-extracted">Extracted</span>
                )}
              </div>
              <input
                type="text"
                value={p.country || ""}
                onChange={(e) => updateNested("personal", "country", e.target.value)}
                placeholder="India / United States"
              />
            </div>

            <div className="profile-input-group">
              <div className="label-row">
                <label>Postal / ZIP Code</label>
                {isExtracted("personal.postal_code") && (
                  <span className="badge-extracted">Extracted</span>
                )}
              </div>
              <input
                type="text"
                value={p.postal_code || ""}
                onChange={(e) => updateNested("personal", "postal_code", e.target.value)}
                placeholder="560001 / 94107"
              />
            </div>

            <div className="profile-input-group full-width">
              <div className="label-row">
                <label>Street Address</label>
              </div>
              <input
                type="text"
                value={p.address || ""}
                onChange={(e) => updateNested("personal", "address", e.target.value)}
                placeholder="123 Tech Park Road, Floor 4"
              />
            </div>
          </div>
        )}

        {/* ================= EDUCATION TAB ================= */}
        {activeTab === "education" && (
          <div className="form-grid-2">
            <div className="profile-input-group full-width">
              <div className="label-row">
                <label>College / University Name</label>
                {isExtracted("education.college_name") && (
                  <span className="badge-extracted">Extracted</span>
                )}
              </div>
              <input
                type="text"
                value={e.college_name || ""}
                onChange={(e) => updateNested("education", "college_name", e.target.value)}
                placeholder="e.g. Stanford University / National Institute of Technology"
              />
            </div>

            <div className="profile-input-group">
              <div className="label-row">
                <label>Degree</label>
                {isExtracted("education.degree") && (
                  <span className="badge-extracted">Extracted</span>
                )}
              </div>
              <input
                type="text"
                value={e.degree || ""}
                onChange={(e) => updateNested("education", "degree", e.target.value)}
                placeholder="Bachelor of Technology / B.S. in Computer Science"
              />
            </div>

            <div className="profile-input-group">
              <div className="label-row">
                <label>Branch / Specialization</label>
                {isExtracted("education.branch_specialization") && (
                  <span className="badge-extracted">Extracted</span>
                )}
              </div>
              <input
                type="text"
                value={e.branch_specialization || ""}
                onChange={(e) => updateNested("education", "branch_specialization", e.target.value)}
                placeholder="Computer Science & Engineering / Artificial Intelligence"
              />
            </div>

            <div className="profile-input-group">
              <div className="label-row">
                <label>Graduation Year</label>
                {isExtracted("education.graduation_year") && (
                  <span className="badge-extracted">Extracted</span>
                )}
              </div>
              <input
                type="text"
                value={e.graduation_year || ""}
                onChange={(e) => updateNested("education", "graduation_year", e.target.value)}
                placeholder="2025"
              />
            </div>

            <div className="profile-input-group">
              <div className="label-row">
                <label>Current Semester / Academic Year</label>
                {isExtracted("education.current_semester") && (
                  <span className="badge-extracted">Extracted</span>
                )}
              </div>
              <input
                type="text"
                value={e.current_semester || ""}
                onChange={(e) => updateNested("education", "current_semester", e.target.value)}
                placeholder="8th Semester / Final Year"
              />
            </div>

            <div className="profile-input-group">
              <div className="label-row">
                <label>GPA / CGPA / Percentage</label>
                {isExtracted("education.gpa_percentage") && (
                  <span className="badge-extracted">Extracted</span>
                )}
              </div>
              <input
                type="text"
                value={e.gpa_percentage || ""}
                onChange={(e) => updateNested("education", "gpa_percentage", e.target.value)}
                placeholder="3.8 / 4.0 or 8.9 / 10"
              />
            </div>
          </div>
        )}

        {/* ================= LINKS TAB ================= */}
        {activeTab === "links" && (
          <div className="form-grid-2">
            <div className="profile-input-group">
              <div className="label-row">
                <label>LinkedIn Profile URL</label>
                {isExtracted("links.linkedin_url") && (
                  <span className="badge-extracted">Extracted</span>
                )}
              </div>
              <input
                type="url"
                value={l.linkedin_url || ""}
                onChange={(e) => updateNested("links", "linkedin_url", e.target.value)}
                placeholder="https://linkedin.com/in/username"
              />
            </div>

            <div className="profile-input-group">
              <div className="label-row">
                <label>GitHub Profile URL</label>
                {isExtracted("links.github_url") && (
                  <span className="badge-extracted">Extracted</span>
                )}
              </div>
              <input
                type="url"
                value={l.github_url || ""}
                onChange={(e) => updateNested("links", "github_url", e.target.value)}
                placeholder="https://github.com/username"
              />
            </div>

            <div className="profile-input-group">
              <div className="label-row">
                <label>Portfolio / Personal Website</label>
                {isExtracted("links.portfolio_url") && (
                  <span className="badge-extracted">Extracted</span>
                )}
              </div>
              <input
                type="url"
                value={l.portfolio_url || ""}
                onChange={(e) => updateNested("links", "portfolio_url", e.target.value)}
                placeholder="https://yourportfolio.dev"
              />
            </div>

            <div className="profile-input-group">
              <div className="label-row">
                <label>Twitter / X Profile URL</label>
                {isExtracted("links.twitter_url") && (
                  <span className="badge-extracted">Extracted</span>
                )}
              </div>
              <input
                type="url"
                value={l.twitter_url || ""}
                onChange={(e) => updateNested("links", "twitter_url", e.target.value)}
                placeholder="https://x.com/username"
              />
            </div>
          </div>
        )}

        {/* ================= PROFESSIONAL & SKILLS TAB ================= */}
        {activeTab === "professional" && (
          <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
            {/* Skills Tag Cloud */}
            <div className="profile-card-sub">
              <div className="label-row" style={{ marginBottom: "10px" }}>
                <label style={{ fontSize: "15px", fontWeight: "600", color: "#fff" }}>
                  Key Technical Skills
                </label>
                {isExtracted("professional.key_skills") && (
                  <span className="badge-extracted">Extracted</span>
                )}
              </div>

              <div style={{ display: "flex", gap: "8px", marginBottom: "14px" }}>
                <input
                  type="text"
                  value={newSkill}
                  onChange={(e) => setNewSkill(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addSkill())}
                  placeholder="Type a skill (e.g. PyTorch, React, Golang) and press Enter"
                  style={{ flex: 1 }}
                />
                <button
                  type="button"
                  onClick={addSkill}
                  className="btn-secondary"
                  style={{ whiteSpace: "nowrap" }}
                >
                  + Add Skill
                </button>
              </div>

              <div className="skills-pill-container">
                {(prof.key_skills || []).map((skill, idx) => (
                  <span key={idx} className="skill-pill-interactive">
                    {skill}
                    <button
                      type="button"
                      onClick={() => removeSkill(skill)}
                      title="Remove skill"
                    >
                      ×
                    </button>
                  </span>
                ))}
                {(!prof.key_skills || prof.key_skills.length === 0) && (
                  <small style={{ color: "#6b7280" }}>No skills added yet.</small>
                )}
              </div>
            </div>

            {/* Experience Years & Summary */}
            <div className="form-grid-2">
              <div className="profile-input-group">
                <div className="label-row">
                  <label>Total Experience (Years)</label>
                  {isExtracted("professional.experience_years") && (
                    <span className="badge-extracted">Extracted</span>
                  )}
                </div>
                <input
                  type="text"
                  value={prof.experience_years || ""}
                  onChange={(e) => updateNested("professional", "experience_years", e.target.value)}
                  placeholder="0 (or 1, 2, 3+)"
                />
              </div>

              <div className="profile-input-group full-width">
                <div className="label-row">
                  <label>Professional Summary / Bio</label>
                  {isExtracted("professional.summary") && (
                    <span className="badge-extracted">Extracted</span>
                  )}
                </div>
                <textarea
                  rows={3}
                  value={prof.summary || ""}
                  onChange={(e) => updateNested("professional", "summary", e.target.value)}
                  placeholder="Passionate AI & software engineer with hands-on experience building scalable applications..."
                />
              </div>
            </div>

            {/* Achievements & Certifications */}
            <div className="form-grid-2">
              <div className="profile-card-sub">
                <label style={{ fontSize: "14px", fontWeight: "600", color: "#fff", display: "block", marginBottom: "8px" }}>
                  Key Achievements
                </label>
                <div style={{ display: "flex", gap: "8px", marginBottom: "10px" }}>
                  <input
                    type="text"
                    value={newAchievement}
                    onChange={(e) => setNewAchievement(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && newAchievement.trim()) {
                        e.preventDefault();
                        const curr = prof.achievements || [];
                        updateNested("professional", "achievements", [...curr, newAchievement.trim()]);
                        setNewAchievement("");
                      }
                    }}
                    placeholder="e.g. 1st Place at National Hackathon 2024"
                  />
                  <button
                    type="button"
                    onClick={() => {
                      if (newAchievement.trim()) {
                        const curr = prof.achievements || [];
                        updateNested("professional", "achievements", [...curr, newAchievement.trim()]);
                        setNewAchievement("");
                      }
                    }}
                    className="btn-secondary"
                  >
                    + Add
                  </button>
                </div>
                <ul className="profile-bullet-list">
                  {(prof.achievements || []).map((ach, idx) => (
                    <li key={idx}>
                      <span>{ach}</span>
                      <button
                        type="button"
                        onClick={() => {
                          const curr = prof.achievements || [];
                          updateNested(
                            "professional",
                            "achievements",
                            curr.filter((_, i) => i !== idx)
                          );
                        }}
                      >
                        ×
                      </button>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="profile-card-sub">
                <label style={{ fontSize: "14px", fontWeight: "600", color: "#fff", display: "block", marginBottom: "8px" }}>
                  Certifications
                </label>
                <div style={{ display: "flex", gap: "8px", marginBottom: "10px" }}>
                  <input
                    type="text"
                    value={newCertification}
                    onChange={(e) => setNewCertification(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && newCertification.trim()) {
                        e.preventDefault();
                        const curr = prof.certifications || [];
                        updateNested("professional", "certifications", [...curr, newCertification.trim()]);
                        setNewCertification("");
                      }
                    }}
                    placeholder="e.g. AWS Certified Developer / DeepLearning.AI Specialization"
                  />
                  <button
                    type="button"
                    onClick={() => {
                      if (newCertification.trim()) {
                        const curr = prof.certifications || [];
                        updateNested("professional", "certifications", [...curr, newCertification.trim()]);
                        setNewCertification("");
                      }
                    }}
                    className="btn-secondary"
                  >
                    + Add
                  </button>
                </div>
                <ul className="profile-bullet-list">
                  {(prof.certifications || []).map((cert, idx) => (
                    <li key={idx}>
                      <span>{cert}</span>
                      <button
                        type="button"
                        onClick={() => {
                          const curr = prof.certifications || [];
                          updateNested(
                            "professional",
                            "certifications",
                            curr.filter((_, i) => i !== idx)
                          );
                        }}
                      >
                        ×
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* ================= PROJECTS TAB ================= */}
        {activeTab === "projects" && (
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <div>
                <h4 style={{ margin: "0 0 4px 0", color: "#fff" }}>
                  Featured Projects ({prof.projects?.length || 0})
                </h4>
                <small style={{ color: "#9ca3af" }}>
                  The AI Question Agent references these verified projects to answer "Explain a project" and technical questions.
                </small>
              </div>
              <button
                type="button"
                className="btn-secondary"
                onClick={() => setShowAddProject(!showAddProject)}
              >
                {showAddProject ? "Cancel" : "+ Add Project"}
              </button>
            </div>

            {/* Add Project Form Drawer */}
            {showAddProject && (
              <div className="profile-card-sub" style={{ marginBottom: "20px", border: "1px solid #6366f1" }}>
                <h5 style={{ margin: "0 0 12px 0", color: "#a5b4fc" }}>New Project Details</h5>
                <div className="form-grid-2">
                  <div className="profile-input-group">
                    <label>Project Title *</label>
                    <input
                      type="text"
                      value={projectDraft.name}
                      onChange={(e) => setProjectDraft({ ...projectDraft, name: e.target.value })}
                      placeholder="e.g. Autonomous Job Application Agent"
                    />
                  </div>
                  <div className="profile-input-group">
                    <label>Project / Repository URL</label>
                    <input
                      type="url"
                      value={projectDraft.url}
                      onChange={(e) => setProjectDraft({ ...projectDraft, url: e.target.value })}
                      placeholder="https://github.com/username/project"
                    />
                  </div>
                  <div className="profile-input-group full-width">
                    <label>Technologies Used (comma separated)</label>
                    <input
                      type="text"
                      value={projectDraft.technologies}
                      onChange={(e) => setProjectDraft({ ...projectDraft, technologies: e.target.value })}
                      placeholder="Python, FastAPI, Playwright, React, LLMs"
                    />
                  </div>
                  <div className="profile-input-group full-width">
                    <label>Description & Key Challenges Solved</label>
                    <textarea
                      rows={3}
                      value={projectDraft.description}
                      onChange={(e) => setProjectDraft({ ...projectDraft, description: e.target.value })}
                      placeholder="Built an autonomous multi-step job application system utilizing Playwright Chromium automation and LLM question answering..."
                    />
                  </div>
                </div>
                <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "12px" }}>
                  <button type="button" onClick={() => setShowAddProject(false)} className="btn-outline">
                    Cancel
                  </button>
                  <button type="button" onClick={handleAddProject} className="btn-primary-glow">
                    Save Project
                  </button>
                </div>
              </div>
            )}

            {/* Projects List */}
            <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
              {(prof.projects || []).map((proj, idx) => (
                <div key={idx} className="project-item-card">
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                    <div>
                      <h4 style={{ margin: "0 0 6px 0", color: "#fff", fontSize: "16px" }}>
                        {proj.name || proj.title || "Project"}
                      </h4>
                      {proj.url && (
                        <a
                          href={proj.url}
                          target="_blank"
                          rel="noreferrer"
                          style={{ fontSize: "12px", color: "#818cf8", textDecoration: "none" }}
                        >
                          {proj.url} ↗
                        </a>
                      )}
                    </div>
                    <button
                      type="button"
                      onClick={() => removeProject(idx)}
                      className="btn-delete-icon"
                      title="Delete Project"
                    >
                      🗑
                    </button>
                  </div>

                  <p style={{ margin: "8px 0", fontSize: "13px", color: "#d1d5db", lineHeight: "1.5" }}>
                    {proj.description || "No description provided."}
                  </p>

                  {proj.technologies && proj.technologies.length > 0 && (
                    <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginTop: "8px" }}>
                      {proj.technologies.map((t, tIdx) => (
                        <span key={tIdx} className="tech-badge">
                          {t}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}

              {(!prof.projects || prof.projects.length === 0) && (
                <div className="empty-substate">
                  <p>No projects listed yet. Click "+ Add Project" to add your notable work.</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ================= EXPERIENCE TAB ================= */}
        {activeTab === "experience" && (
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <div>
                <h4 style={{ margin: "0 0 4px 0", color: "#fff" }}>
                  Work & Internship Experience ({prof.experience?.length || 0})
                </h4>
                <small style={{ color: "#9ca3af" }}>
                  Truthful work history used for questions regarding past responsibilities and impact.
                </small>
              </div>
              <button
                type="button"
                className="btn-secondary"
                onClick={() => setShowAddExp(!showAddExp)}
              >
                {showAddExp ? "Cancel" : "+ Add Experience"}
              </button>
            </div>

            {/* Add Experience Form */}
            {showAddExp && (
              <div className="profile-card-sub" style={{ marginBottom: "20px", border: "1px solid #6366f1" }}>
                <h5 style={{ margin: "0 0 12px 0", color: "#a5b4fc" }}>New Experience Details</h5>
                <div className="form-grid-2">
                  <div className="profile-input-group">
                    <label>Company / Organization *</label>
                    <input
                      type="text"
                      value={expDraft.company}
                      onChange={(e) => setExpDraft({ ...expDraft, company: e.target.value })}
                      placeholder="e.g. Innovate AI"
                    />
                  </div>
                  <div className="profile-input-group">
                    <label>Role / Title</label>
                    <input
                      type="text"
                      value={expDraft.role}
                      onChange={(e) => setExpDraft({ ...expDraft, role: e.target.value })}
                      placeholder="e.g. Software Engineer Intern"
                    />
                  </div>
                  <div className="profile-input-group full-width">
                    <label>Duration / Dates</label>
                    <input
                      type="text"
                      value={expDraft.duration}
                      onChange={(e) => setExpDraft({ ...expDraft, duration: e.target.value })}
                      placeholder="e.g. May 2024 - August 2024 (4 months)"
                    />
                  </div>
                  <div className="profile-input-group full-width">
                    <label>Responsibilities & Achievements</label>
                    <textarea
                      rows={3}
                      value={expDraft.description}
                      onChange={(e) => setExpDraft({ ...expDraft, description: e.target.value })}
                      placeholder="Developed backend APIs and optimized query latency by 35%..."
                    />
                  </div>
                </div>
                <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "12px" }}>
                  <button type="button" onClick={() => setShowAddExp(false)} className="btn-outline">
                    Cancel
                  </button>
                  <button type="button" onClick={handleAddExperience} className="btn-primary-glow">
                    Save Experience
                  </button>
                </div>
              </div>
            )}

            {/* Experience List */}
            <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
              {(prof.experience || []).map((exp, idx) => (
                <div key={idx} className="project-item-card">
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                    <div>
                      <h4 style={{ margin: "0 0 4px 0", color: "#fff", fontSize: "16px" }}>
                        {exp.role || exp.title || "Engineer"} &bull; <span style={{ color: "#a5b4fc" }}>{exp.company}</span>
                      </h4>
                      {exp.duration && (
                        <span style={{ fontSize: "12px", color: "#9ca3af" }}>
                          🕒 {exp.duration}
                        </span>
                      )}
                    </div>
                    <button
                      type="button"
                      onClick={() => removeExperience(idx)}
                      className="btn-delete-icon"
                      title="Delete Experience"
                    >
                      🗑
                    </button>
                  </div>

                  <p style={{ margin: "10px 0 0 0", fontSize: "13px", color: "#d1d5db", lineHeight: "1.5" }}>
                    {exp.description || "No description provided."}
                  </p>
                </div>
              ))}

              {(!prof.experience || prof.experience.length === 0) && (
                <div className="empty-substate">
                  <p>No prior work experience listed. Click "+ Add Experience" if applicable.</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ================= PREFERENCES TAB ================= */}
        {activeTab === "preferences" && (
          <div className="form-grid-2">
            <div className="profile-input-group full-width">
              <label>Work Authorization Declaration</label>
              <input
                type="text"
                value={pref.work_authorization || ""}
                onChange={(e) => updateNested("preferences", "work_authorization", e.target.value)}
                placeholder="e.g. Authorized to work in India / US without sponsorship"
              />
              <small style={{ color: "#6b7280", marginTop: "4px", display: "block" }}>
                Used to answer standard eligibility and work authorization fields automatically.
              </small>
            </div>

            <div className="profile-input-group">
              <label>Willing to Relocate?</label>
              <select
                value={pref.willing_to_relocate || "Yes"}
                onChange={(e) => updateNested("preferences", "willing_to_relocate", e.target.value)}
              >
                <option value="Yes">Yes</option>
                <option value="No">No</option>
                <option value="Open for Remote or Hybrid only">Open for Remote or Hybrid only</option>
              </select>
            </div>

            <div className="profile-input-group">
              <label>Notice Period / Availability</label>
              <input
                type="text"
                value={pref.notice_period || ""}
                onChange={(e) => updateNested("preferences", "notice_period", e.target.value)}
                placeholder="Immediate / 15 Days / 1 Month"
              />
            </div>

            <div className="profile-input-group">
              <label>Expected Salary / Stipend</label>
              <input
                type="text"
                value={pref.expected_salary_stipend || ""}
                onChange={(e) => updateNested("preferences", "expected_salary_stipend", e.target.value)}
                placeholder="e.g. ₹50,000/mo or $85,000/yr (or Open/Negotiable)"
              />
            </div>

            <div className="profile-input-group">
              <label>Remote Preference</label>
              <select
                value={pref.remote_preference || "Remote"}
                onChange={(e) => updateNested("preferences", "remote_preference", e.target.value)}
              >
                <option value="Remote">Remote</option>
                <option value="Hybrid">Hybrid</option>
                <option value="On-site">On-site</option>
                <option value="Any">Any</option>
              </select>
            </div>
          </div>
        )}

        {/* ================= CUSTOM FIELDS TAB ================= */}
        {activeTab === "custom" && (
          <div>
            <div style={{ marginBottom: "16px" }}>
              <h4 style={{ margin: "0 0 4px 0", color: "#fff" }}>
                Extensible Custom Fields & Application Answers
              </h4>
              <small style={{ color: "#9ca3af" }}>
                Add custom key-value pairs or recurring questions here. They will automatically be matched and filled by the agent.
              </small>
            </div>

            <div className="profile-card-sub" style={{ marginBottom: "20px" }}>
              <h5 style={{ margin: "0 0 10px 0", color: "#a5b4fc" }}>+ Add New Dynamic Profile Field</h5>
              <div className="form-grid-2">
                <div className="profile-input-group">
                  <label>Field Name / Identifier</label>
                  <input
                    type="text"
                    value={newCustomKey}
                    onChange={(e) => setNewCustomKey(e.target.value)}
                    placeholder="e.g. leetcode_url, kaggle_profile, discord_handle"
                  />
                </div>
                <div className="profile-input-group">
                  <label>Field Value</label>
                  <input
                    type="text"
                    value={newCustomVal}
                    onChange={(e) => setNewCustomVal(e.target.value)}
                    placeholder="e.g. https://leetcode.com/username"
                  />
                </div>
              </div>
              <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "10px" }}>
                <button
                  type="button"
                  onClick={addCustomField}
                  disabled={!newCustomKey.trim()}
                  className="btn-secondary"
                >
                  + Add Custom Field
                </button>
              </div>
            </div>

            {/* Custom fields list */}
            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              {Object.entries(custom).map(([key, value], idx) => (
                <div key={idx} className="custom-field-row">
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <strong style={{ color: "#a5b4fc", fontSize: "14px", display: "block" }}>
                      {key}
                    </strong>
                    <span style={{ color: "#e5e7eb", fontSize: "13px" }}>
                      {String(value)}
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={() => removeCustomField(key)}
                    className="btn-delete-icon"
                    title="Remove custom field"
                  >
                    ×
                  </button>
                </div>
              ))}

              {Object.keys(custom).length === 0 && (
                <div className="empty-substate">
                  <p>No custom fields added yet. Add custom links, ATS-specific answers, or unique identifiers above.</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
