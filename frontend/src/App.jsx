// src/App.jsx

import { useState, useEffect } from "react";
import {
  searchJobs,
  startApplicationAgent,
  confirmApplicationSubmit,
  getSavedJobs,
  getSavedProfile,
  getApplications,
  clearSavedJobs,
} from "./services/api";
import JobCard from "./components/JobCard";
import PlacementCalendar from "./components/PlacementCalendar";
import Hero from "./components/Hero";
import CandidateProfileView from "./components/CandidateProfileView";
import AgentSettingsBar from "./components/AgentSettingsBar";
import ApplicationDetailModal from "./components/ApplicationDetailModal";
import "./index.css";

const API_BASE = "http://127.0.0.1:8000";

function App() {
  const [view, setView] = useState("landing"); // "landing" or "dashboard"
  const [resume, setResume] = useState(null);
  const [resumeName, setResumeName] = useState("");
  const [resumePath, setResumePath] = useState("");
  const [profileData, setProfileData] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [applications, setApplications] = useState([]);
  const [role, setRole] = useState("");
  const [location, setLocation] = useState("");

  const [loading, setLoading] = useState(false);
  const [uploadingResume, setUploadingResume] = useState(false);
  const [clearingJobs, setClearingJobs] = useState(false);

  const [resumeUploaded, setResumeUploaded] = useState(false);
  const [searchError, setSearchError] = useState("");
  const [initLoaded, setInitLoaded] = useState(false);

  const [activePage, setActivePage] = useState("dashboard");

  // Application Agent & Review Modal State
  const [agentJob, setAgentJob] = useState(null);
  const [agentStatus, setAgentStatus] = useState("");
  const [agentStep, setAgentStep] = useState(0);
  const [agentAppId, setAgentAppId] = useState(null);
  const [agentRunning, setAgentRunning] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [submittingConfirm, setSubmittingConfirm] = useState(false);

  // Application Fields Debug Modal
  const [selectedAppForDetail, setSelectedAppForDetail] = useState(null);

  /*
  ============================================================
  LOAD PERSISTENT DATABASE DATA ON MOUNT (Survives Refreshes)
  ============================================================
  */
  useEffect(() => {
    async function loadInitialData() {
      try {
        const profileRes = await getSavedProfile();
        if (profileRes && profileRes.profile) {
          setProfileData(profileRes.profile);
          setResumeUploaded(true);
          setResumeName(profileRes.resume_filename || "Saved Candidate Profile (Database)");
          setResumePath(profileRes.resume_path || "");
        }

        const savedJobs = await getSavedJobs();
        if (savedJobs && savedJobs.length > 0) {
          setJobs(savedJobs);
        }

        const savedApps = await getApplications();
        if (savedApps) {
          setApplications(savedApps);
        }
      } catch (err) {
        console.error("Error loading database records:", err);
      } finally {
        setInitLoaded(true);
      }
    }

    loadInitialData();
  }, []);

  /*
  ============================================================
  RESUME UPLOAD (Persisted in SQLite DB & Extracted)
  ============================================================
  */
  const handleResume = async (e) => {
    const file = e.target.files?.[0];

    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      alert("Please upload a PDF resume.");
      e.target.value = "";
      return;
    }

    setResume(file);
    setResumeName(file.name);
    setResumeUploaded(false);
    setSearchError("");
    setUploadingResume(true);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(`${API_BASE}/api/resume/upload`, {
        method: "POST",
        body: formData,
      });

      let data = {};
      try {
        data = await response.json();
      } catch {
        data = {};
      }

      if (!response.ok) {
        throw new Error(
          data.detail || `Resume upload failed with status ${response.status}`
        );
      }

      setResumeUploaded(true);
      if (data.profile) {
        setProfileData(data.profile);
      }
      if (data.resume_path) {
        setResumePath(data.resume_path);
      }
    } catch (error) {
      console.error("Resume upload failed:", error);
      setResumeUploaded(false);
      setSearchError(error.message || "Unable to upload your resume.");
    } finally {
      setUploadingResume(false);
    }
  };

  /*
  ============================================================
  SEARCH JOBS VIA TAVILY (Max 3 Direct Posts)
  ============================================================
  */
  const handleSearch = async () => {
    if (!resumeUploaded && !resume && !profileData) {
      setSearchError("Please upload your resume or configure profile before searching.");
      return;
    }

    setLoading(true);
    setSearchError("");

    try {
      const result = await searchJobs(resume, role, location);
      setJobs(result);
      setActivePage("jobs");
    } catch (error) {
      console.error("Search failed:", error);
      setSearchError(error.message || "Unable to search for jobs.");
    } finally {
      setLoading(false);
    }
  };

  /*
  ============================================================
  CLEAR JOBS FROM DATABASE
  ============================================================
  */
  const handleClearJobs = async () => {
    if (!window.confirm("Are you sure you want to clear saved jobs?")) return;
    setClearingJobs(true);
    try {
      await clearSavedJobs();
      setJobs([]);
    } catch (err) {
      console.error("Failed to clear jobs:", err);
    } finally {
      setClearingJobs(false);
    }
  };

  /*
  ============================================================
  APPLICATION AGENT (Live Visible Browser Automation)
  ============================================================
  */
  const handleApply = async (job) => {
    setAgentJob(job);
    setAgentRunning(true);
    setIsSubmitted(false);
    setAgentStep(1);
    setAgentStatus("🚀 Launching visible Chromium browser on your screen via Playwright...");

    try {
      const res = await startApplicationAgent(job);
      if (res && res.application_id) {
        setAgentAppId(res.application_id);
      }

      setTimeout(() => {
        setAgentStep(2);
        setAgentStatus(`Chromium is navigating to ${job.company || "Company"} application form...`);
      }, 2000);

      setTimeout(() => {
        setAgentStep(3);
        setAgentStatus("AI Agent is inspecting DOM & autofilling Candidate Profile fields...");
      }, 4500);

      setTimeout(() => {
        setAgentStep(4);
        setAgentStatus("Intelligent LLM Agent answering role questions & attaching resume...");
      }, 7000);

      setTimeout(async () => {
        setAgentStep(5);
        setAgentStatus("Application populated! Paused at READY_FOR_REVIEW for your submission.");
        const updatedApps = await getApplications();
        if (updatedApps) setApplications(updatedApps);
      }, 9500);
    } catch (error) {
      console.error("Agent failed:", error);
      setAgentStatus("Agent started. Visible Chromium browser is running...");
    }
  };

  /*
  ============================================================
  USER HUMAN-IN-THE-LOOP SUBMIT APPROVAL
  ============================================================
  */
  const handleConfirmSubmit = async () => {
    setSubmittingConfirm(true);
    try {
      await confirmApplicationSubmit(agentAppId, agentJob?.url || agentJob?.job_url);
      setIsSubmitted(true);
      setAgentStatus("🎉 Application confirmed and recorded in database!");

      const updatedApps = await getApplications();
      if (updatedApps) setApplications(updatedApps);
    } catch (err) {
      console.error("Failed to confirm submission:", err);
      setIsSubmitted(true);
    } finally {
      setSubmittingConfirm(false);
    }
  };

  if (view === "landing") {
    return <Hero onLaunchAgent={() => setView("dashboard")} />;
  }

  return (
    <div className="app">
      {/* SIDEBAR */}
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">✦</div>
          <div>
            <h2>JobMate</h2>
            <span>Autonomous AI Agent</span>
          </div>
        </div>

        <nav>
          {[
            { id: "dashboard", icon: "⌂", label: "Dashboard" },
            { id: "placement", icon: "🎯", label: "Placement Radar" },
            {
              id: "jobs",
              icon: "◉",
              label: `Jobs (${jobs.length})`,
            },
            {
              id: "applications",
              icon: "✓",
              label: `Applications (${applications.length})`,
            },
            { id: "resume", icon: "▣", label: "Candidate Profile" },
          ].map((item) => (
            <button
              key={item.id}
              className={`nav ${activePage === item.id ? "active" : ""}`}
              onClick={() => setActivePage(item.id)}
            >
              <span>{item.icon}</span>
              {item.label}
            </button>
          ))}

          <button
            className="nav"
            style={{
              marginTop: "12px",
              borderTop: "1px solid rgba(255, 255, 255, 0.08)",
              paddingTop: "12px",
              color: "#a5b4fc",
            }}
            onClick={() => setView("landing")}
            title="View the Cinematic Story Landing Page"
          >
            <span>✨</span>
            Story Experience
          </button>
        </nav>

        <div className="agent-status">
          <div className="status-dot"></div>
          <div>
            <strong>SQLite Synced</strong>
            <small>{jobs.length} jobs &bull; {applications.length} apps</small>
          </div>
        </div>
      </aside>

      {/* MAIN CONTENT */}
      <main className="main">
        <header className="header">
          <div>
            <p className="eyebrow">AUTONOMOUS CANDIDATE PROFILE & AUTO-APPLY AGENT</p>
            <h1>
              Find your next
              <span> opportunity.</span>
            </h1>
          </div>

          <div className="header-right">
            <div className="online">
              <span></span>
              Database Connected
            </div>
          </div>
        </header>

        {/* Global Agent Safety Controls Bar */}
        <AgentSettingsBar />

        {/* DASHBOARD */}
        {activePage === "dashboard" && (
          <>
            <section className="hero">
              <div className="hero-content">
                <div className="hero-badge">
                  ✦ Persistent Candidate Profile + Intelligent LLM Question Agent
                </div>
                <h2>
                  Configure once.
                  <br />
                  <span>Apply anywhere.</span>
                </h2>
                <p>
                  Upload your resume to automatically generate your persistent Candidate Profile. The LLM Question Agent intelligently answers company questions, explains your projects, and validates word limits in visible Playwright Chromium.
                </p>
                <div style={{ marginTop: "16px", display: "flex", gap: "10px", flexWrap: "wrap" }}>
                  <button
                    onClick={() => setActivePage("resume")}
                    style={{
                      padding: "10px 18px",
                      borderRadius: "10px",
                      background: "linear-gradient(135deg, #8d6bff, #6240ff)",
                      border: "none",
                      color: "#fff",
                      fontWeight: "600",
                      fontSize: "13px",
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      gap: "6px",
                    }}
                  >
                    <span>▣</span> View / Edit Candidate Profile
                  </button>

                  <button
                    onClick={() => setActivePage("placement")}
                    style={{
                      padding: "10px 18px",
                      borderRadius: "10px",
                      background: "rgba(255, 255, 255, 0.06)",
                      border: "1px solid rgba(255, 255, 255, 0.15)",
                      color: "#e5e7eb",
                      fontWeight: "600",
                      fontSize: "13px",
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      gap: "6px",
                    }}
                  >
                    <span>🎯</span> Open Placement Radar
                  </button>
                </div>
              </div>

              <div className="hero-orb">
                <div className="orb-inner">✦</div>
              </div>
            </section>

            {/* SEARCH CARD */}
            <section className="search-card">
              <div className="section-heading">
                <div>
                  <span className="number">01</span>
                  <h3>Tell your agent what you're looking for</h3>
                </div>
              </div>

              <div className="form-grid">
                <div className="input-group">
                  <label>Target role</label>
                  <div className="input-wrapper">
                    <span>⌕</span>
                    <input
                      value={role}
                      onChange={(e) => setRole(e.target.value)}
                      placeholder="AI/ML Engineer, Fullstack, Python SWE..."
                    />
                  </div>
                </div>

                <div className="input-group">
                  <label>Location</label>
                  <div className="input-wrapper">
                    <span>⌖</span>
                    <input
                      value={location}
                      onChange={(e) => setLocation(e.target.value)}
                      placeholder="Remote, India, Europe, Global..."
                    />
                  </div>
                </div>
              </div>

              {/* RESUME UPLOAD */}
              <div className="resume-upload">
                <input
                  type="file"
                  id="resume"
                  accept=".pdf"
                  onChange={handleResume}
                  hidden
                />

                <label htmlFor="resume" className="upload-box">
                  <div className="upload-icon">↑</div>

                  <div>
                    {resumeName || resume || profileData?.personal?.full_name ? (
                      <>
                        <strong>
                          {resumeName || resume?.name || (profileData?.personal?.full_name ? `${profileData.personal.full_name}'s Profile` : "Saved Resume")}
                        </strong>
                        <small>
                          {uploadingResume
                            ? "Uploading & extracting structured profile to database..."
                            : resumeUploaded || profileData
                            ? "Candidate Profile synced in database & ready for application filling"
                            : "Resume selected"}
                        </small>
                      </>
                    ) : (
                      <>
                        <strong>Upload your resume</strong>
                        <small>PDF • Automatically populates your persistent Candidate Profile</small>
                      </>
                    )}
                  </div>

                  <span className="upload-action">
                    {uploadingResume
                      ? "Extracting..."
                      : resumeUploaded || profileData
                      ? "Replace"
                      : "Browse"}
                  </span>
                </label>
              </div>

              {/* SEARCH BUTTON */}
              <div style={{ display: "flex", gap: "12px", marginTop: "16px", flexWrap: "wrap" }}>
                <button
                  className="search-button"
                  onClick={handleSearch}
                  disabled={loading || uploadingResume}
                  style={{ flex: 1, minWidth: "220px" }}
                >
                  {uploadingResume ? (
                    <>
                      <span className="spinner"></span>
                      Extracting resume profile...
                    </>
                  ) : loading ? (
                    <>
                      <span className="spinner"></span>
                      Searching live Tavily ATS job posts...
                    </>
                  ) : (
                    <>
                      Search 3 Matching Jobs (Tavily)
                      <span>→</span>
                    </>
                  )}
                </button>

                {jobs.length > 0 && (
                  <button
                    className="search-button"
                    onClick={() => setActivePage("jobs")}
                    style={{
                      background: "rgba(255, 255, 255, 0.08)",
                      borderColor: "rgba(255, 255, 255, 0.15)",
                    }}
                  >
                    View Matching Jobs ({jobs.length})
                  </button>
                )}
              </div>

              {searchError && (
                <div className="error-box">⚠ {searchError}</div>
              )}
            </section>

            {/* DIRECT MATCHING JOBS SECTION ON DASHBOARD */}
            {jobs.length > 0 && (
              <section className="page-section" style={{ marginTop: "28px" }}>
                <div className="page-title">
                  <div>
                    <p className="eyebrow">TAVILY VERIFIED ATS OPPORTUNITIES</p>
                    <h2>Direct Matching Job Postings ({jobs.length})</h2>
                  </div>

                  <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
                    <span className="job-count">
                      {jobs.length} Verified Direct Posts
                    </span>
                    <button
                      onClick={handleClearJobs}
                      disabled={clearingJobs}
                      style={{
                        background: "transparent",
                        border: "1px solid rgba(255, 80, 80, 0.3)",
                        color: "#ff6b6b",
                        borderRadius: "8px",
                        padding: "6px 14px",
                        fontSize: "13px",
                        cursor: "pointer",
                      }}
                    >
                      {clearingJobs ? "Clearing..." : "Clear"}
                    </button>
                  </div>
                </div>

                <div className="jobs-list">
                  {jobs.map((job, index) => (
                    <JobCard
                      key={job.id || job.job_url || job.url || index}
                      job={job}
                      onApply={() => handleApply(job)}
                    />
                  ))}
                </div>
              </section>
            )}
          </>
        )}

        {/* PLACEMENT CALENDAR & TARGET HUB */}
        {activePage === "placement" && (
          <section className="page-section">
            <PlacementCalendar onApplyWithAgent={handleApply} />
          </section>
        )}

        {/* JOBS PAGE */}
        {activePage === "jobs" && (
          <section className="page-section">
            <div className="page-title">
              <div>
                <p className="eyebrow">TAVILY LIVE ATS SEARCH RESULTS</p>
                <h2>Matching Job Posts</h2>
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: "12px", flexWrap: "wrap" }}>
                <span className="job-count">
                  {jobs.length} direct job posts found
                </span>
                {jobs.length > 0 && (
                  <button
                    onClick={handleClearJobs}
                    disabled={clearingJobs}
                    style={{
                      background: "transparent",
                      border: "1px solid rgba(255, 80, 80, 0.3)",
                      color: "#ff6b6b",
                      borderRadius: "8px",
                      padding: "6px 14px",
                      fontSize: "13px",
                      cursor: "pointer",
                    }}
                  >
                    {clearingJobs ? "Clearing..." : "Clear Database"}
                  </button>
                )}
              </div>
            </div>

            {jobs.length === 0 ? (
              <div className="empty-state">
                <div>⌕</div>
                <h3>No jobs saved in database yet</h3>
                <p>
                  Go to the dashboard and search with your resume. Real direct ATS openings will appear here.
                </p>
                <div style={{ display: "flex", gap: "10px", marginTop: "12px" }}>
                  <button onClick={() => setActivePage("dashboard")}>
                    Search Jobs Now →
                  </button>
                  <button
                    onClick={() => setActivePage("placement")}
                    style={{
                      background: "rgba(109, 75, 255, 0.2)",
                      border: "1px solid #8d6bff",
                      color: "#b9a2ff",
                    }}
                  >
                    Explore Target Radar ↗
                  </button>
                </div>
              </div>
            ) : (
              <div className="jobs-list">
                {jobs.map((job, index) => (
                  <JobCard
                    key={job.id || job.url || index}
                    job={job}
                    onApply={() => handleApply(job)}
                  />
                ))}
              </div>
            )}
          </section>
        )}

        {/* APPLICATIONS HISTORY WITH DEBUG FIELD TRACE */}
        {activePage === "applications" && (
          <section className="page-section">
            <div className="page-title">
              <div>
                <p className="eyebrow">AUTOMATED APPLICATION SESSIONS</p>
                <h2>Applications History</h2>
              </div>
              <span className="job-count">
                {applications.length} recorded
              </span>
            </div>

            {applications.length === 0 ? (
              <div className="empty-state">
                <div>✓</div>
                <h3>No applications logged yet</h3>
                <p>
                  Click "Apply with AI" on any job to launch visible Playwright automation and LLM question answering.
                </p>
                <button onClick={() => setActivePage("jobs")}>
                  Browse Saved Jobs →
                </button>
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginTop: "20px" }}>
                {applications.map((app) => (
                  <div
                    key={app.id}
                    style={{
                      background: "#111116",
                      border: "1px solid #24242b",
                      borderRadius: "12px",
                      padding: "16px 20px",
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      flexWrap: "wrap",
                      gap: "12px",
                    }}
                  >
                    <div style={{ minWidth: 0, flex: 1 }}>
                      <h4 style={{ margin: "0 0 4px 0", fontSize: "16px", color: "#fff", wordBreak: "break-word" }}>
                        {app.job_title || "Job Application"}
                      </h4>
                      <div style={{ fontSize: "13px", color: "#85858d", display: "flex", flexWrap: "wrap", gap: "12px" }}>
                        {app.company && <span>🏢 {app.company}</span>}
                        <span>🕒 {app.timestamp}</span>
                        {app.job_url && (
                          <a
                            href={app.job_url}
                            target="_blank"
                            rel="noreferrer"
                            style={{ color: "#8d6bff", textDecoration: "none", wordBreak: "break-all" }}
                          >
                            Job Post Link ↗
                          </a>
                        )}
                      </div>
                    </div>

                    <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                      <button
                        onClick={() => setSelectedAppForDetail(app)}
                        style={{
                          background: "rgba(141, 107, 255, 0.12)",
                          border: "1px solid rgba(141, 107, 255, 0.3)",
                          color: "#c7d2fe",
                          borderRadius: "8px",
                          padding: "6px 12px",
                          fontSize: "12px",
                          fontWeight: "600",
                          cursor: "pointer",
                        }}
                      >
                        🔍 Inspect Fields
                      </button>

                      <span
                        style={{
                          padding: "4px 12px",
                          borderRadius: "20px",
                          fontSize: "12px",
                          fontWeight: "600",
                          textTransform: "uppercase",
                          flexShrink: 0,
                          background:
                            app.status === "SUBMITTED" || app.status === "submitted"
                              ? "rgba(46, 213, 115, 0.15)"
                              : app.status === "READY_FOR_REVIEW" || app.status === "ready_for_review"
                              ? "rgba(255, 165, 2, 0.15)"
                              : app.status === "APPLY_STARTED" || app.status === "running"
                              ? "rgba(109, 75, 255, 0.2)"
                              : "rgba(255, 71, 87, 0.15)",
                          color:
                            app.status === "SUBMITTED" || app.status === "submitted"
                              ? "#2ed573"
                              : app.status === "READY_FOR_REVIEW" || app.status === "ready_for_review"
                              ? "#ffa502"
                              : app.status === "APPLY_STARTED" || app.status === "running"
                              ? "#a388ff"
                              : "#ff4757",
                        }}
                      >
                        {app.status === "READY_FOR_REVIEW" || app.status === "ready_for_review"
                          ? "Reviewed & Filled"
                          : app.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        )}

        {/* PERSISTENT DYNAMIC CANDIDATE PROFILE */}
        {activePage === "resume" && (
          <section className="page-section">
            <CandidateProfileView
              initialProfile={profileData}
              resumeName={resumeName}
              resumePath={resumePath}
              onProfileUpdated={(updated) => setProfileData(updated)}
              onUploadNewResume={() => {
                const el = document.getElementById("resume");
                if (el) el.click();
              }}
            />
          </section>
        )}
      </main>

      {/* Field Inspection Detail Modal */}
      {selectedAppForDetail && (
        <ApplicationDetailModal
          application={selectedAppForDetail}
          onClose={() => setSelectedAppForDetail(null)}
        />
      )}

      {/* =========================================================
          LIVE AGENT FLOATING STATUS BAR (NON-BLOCKING)
      ========================================================= */}
      {agentRunning && (
        <div
          style={{
            position: "fixed",
            bottom: "24px",
            right: "24px",
            background: "#12121a",
            border: "1px solid #382d6e",
            boxShadow: "0 12px 40px rgba(0, 0, 0, 0.6), 0 0 20px rgba(141, 107, 255, 0.2)",
            borderRadius: "14px",
            padding: "16px 20px",
            maxWidth: "460px",
            width: "calc(100% - 48px)",
            zIndex: 9999,
            display: "flex",
            flexDirection: "column",
            gap: "12px",
            animation: "slideUp 0.3s ease",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <span
                style={{
                  width: "10px",
                  height: "10px",
                  borderRadius: "50%",
                  background: isSubmitted ? "#2ed573" : "#8d6bff",
                  boxShadow: `0 0 10px ${isSubmitted ? "#2ed573" : "#8d6bff"}`,
                  display: "inline-block",
                }}
              />
              <div>
                <strong style={{ fontSize: "14px", color: "#fff", display: "block" }}>
                  {isSubmitted ? "Application Logged" : "Visible Playwright Auto-Apply"}
                </strong>
                <span style={{ fontSize: "12px", color: "#9c9ca8" }}>
                  {agentJob?.title || "Role"} &bull; <span style={{ color: "#b9a2ff" }}>{agentJob?.company || "Employer"}</span>
                </span>
              </div>
            </div>

            <button
              onClick={() => setAgentRunning(false)}
              style={{
                background: "transparent",
                border: "none",
                color: "#6c6c78",
                fontSize: "18px",
                cursor: "pointer",
                padding: "0 4px",
              }}
            >
              ×
            </button>
          </div>

          <div
            style={{
              background: "#0a0a0f",
              border: "1px solid #1e1e28",
              borderRadius: "8px",
              padding: "10px 12px",
              fontSize: "12px",
              color: isSubmitted ? "#2ed573" : "#d0d0dc",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            <span>{isSubmitted ? "✓" : "⚡"}</span>
            <span style={{ flex: 1 }}>{agentStatus}</span>
          </div>

          <div style={{ display: "flex", gap: "8px", justifyContent: "flex-end" }}>
            {(agentJob?.apply_url || agentJob?.job_url || agentJob?.url) && (
              <a
                href={agentJob.apply_url || agentJob.job_url || agentJob.url}
                target="_blank"
                rel="noreferrer"
                style={{
                  padding: "8px 12px",
                  borderRadius: "8px",
                  background: "#1a1a24",
                  border: "1px solid #282836",
                  color: "#a48eff",
                  fontSize: "12px",
                  fontWeight: "600",
                  textDecoration: "none",
                  display: "flex",
                  alignItems: "center",
                  gap: "4px",
                }}
              >
                Employer Link ↗
              </a>
            )}
            {!isSubmitted ? (
              <button
                onClick={handleConfirmSubmit}
                disabled={submittingConfirm}
                style={{
                  padding: "8px 14px",
                  borderRadius: "8px",
                  border: "none",
                  background: "linear-gradient(135deg, #2ed573, #10ac84)",
                  color: "#000",
                  fontWeight: "700",
                  fontSize: "12px",
                  cursor: "pointer",
                }}
              >
                {submittingConfirm ? "Saving..." : "✓ Mark Submitted"}
              </button>
            ) : (
              <button
                onClick={() => setAgentRunning(false)}
                style={{
                  padding: "8px 14px",
                  borderRadius: "8px",
                  border: "none",
                  background: "#2ed573",
                  color: "#000",
                  fontWeight: "700",
                  fontSize: "12px",
                  cursor: "pointer",
                }}
              >
                Done
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;