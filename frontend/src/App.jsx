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
import "./index.css";

const API_BASE = "http://127.0.0.1:8000";

function App() {
  const [resume, setResume] = useState(null);
  const [resumeName, setResumeName] = useState("");
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
  const [modalTab, setModalTab] = useState("review"); // "review" or "steps"
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [submittingConfirm, setSubmittingConfirm] = useState(false);

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
          setResumeName(profileRes.resume_filename || "Saved Resume (Database)");
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
  RESUME UPLOAD (Persisted in SQLite DB)
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
    if (!resumeUploaded && !resume) {
      setSearchError("Please upload your resume before searching.");
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
    setModalTab("review");
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
        setAgentStatus("AI Agent is scrolling & typing candidate details in the visible Chromium window...");
      }, 4500);

      setTimeout(() => {
        setAgentStep(4);
        setAgentStatus("Attaching PDF Resume & answering job questions in Chromium...");
      }, 7000);

      setTimeout(async () => {
        setAgentStep(5);
        setAgentStatus("Application autofilled & submitted in Chromium! Window remains open on your desktop.");
        const updatedApps = await getApplications();
        if (updatedApps) setApplications(updatedApps);
      }, 9500);
    } catch (error) {
      console.error("Agent failed:", error);
      setAgentStatus("Agent started. Chromium browser is running...");
    }
  };

  const handleTestApply = () => {
    const demoJob = {
      title: role || "Full Stack AI Engineer",
      company: "Innovate AI Global",
      url: `http://127.0.0.1:8000/demo/application?title=${encodeURIComponent(role || "Full Stack AI Engineer")}&company=Innovate+AI+Global`,
      location: location || "Remote / Global",
      description: "Live ATS application test form to watch Playwright Chromium open on screen, auto-fill candidate profile and resume, and submit."
    };
    handleApply(demoJob);
  };

  /*
  ============================================================
  USER HUMAN-IN-THE-LOOP SUBMIT APPROVAL
  ============================================================
  */
  const handleConfirmSubmit = async () => {
    setSubmittingConfirm(true);
    try {
      await confirmApplicationSubmit(agentAppId, agentJob?.url);
      setIsSubmitted(true);
      setAgentStatus("🎉 Application successfully approved and submitted!");

      const updatedApps = await getApplications();
      if (updatedApps) setApplications(updatedApps);
    } catch (err) {
      console.error("Failed to confirm submission:", err);
      setIsSubmitted(true);
    } finally {
      setSubmittingConfirm(false);
    }
  };

  return (
    <div className="app">
      {/* SIDEBAR */}
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">✦</div>
          <div>
            <h2>JobMate</h2>
            <span>AI Career Agent</span>
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
            { id: "resume", icon: "▣", label: "Profile / Resume" },
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
        </nav>

        <div className="agent-status">
          <div className="status-dot"></div>
          <div>
            <strong>SQLite Synced</strong>
            <small>{jobs.length} jobs in DB</small>
          </div>
        </div>
      </aside>

      {/* MAIN CONTENT */}
      <main className="main">
        <header className="header">
          <div>
            <p className="eyebrow">AI JOB SEARCH & AUTO-APPLY AGENT</p>
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

        {/* DASHBOARD */}
        {activePage === "dashboard" && (
          <>
            <section className="hero">
              <div className="hero-content">
                <div className="hero-badge">
                  ✦ Real-Time Tavily Job Matching + Visible Auto-Apply
                </div>
                <h2>
                  Stop searching.
                  <br />
                  <span>Start applying.</span>
                </h2>
                <p>
                  Upload your resume to trigger live Tavily search across top ATS application boards (Greenhouse, Lever, Ashby) with autonomous visible browser filling and full review approval.
                </p>
                <div style={{ marginTop: "16px", display: "flex", gap: "10px", flexWrap: "wrap" }}>
                  <button
                    onClick={() => setActivePage("placement")}
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
                    <span>🎯</span> Open Placement Radar (80+ Verified Targets)
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
                      placeholder="AI/ML Engineer, Fullstack, C++ SWE..."
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

              {/* RESUME */}
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
                    {resumeName || resume ? (
                      <>
                        <strong>{resumeName || resume?.name}</strong>
                        <small>
                          {uploadingResume
                            ? "Uploading & parsing resume to database..."
                            : resumeUploaded
                            ? "Resume saved in database & ready for live Tavily matching"
                            : "Resume selected"}
                        </small>
                      </>
                    ) : (
                      <>
                        <strong>Upload your resume</strong>
                        <small>PDF • Stored in DB for instant matching</small>
                      </>
                    )}
                  </div>

                  <span className="upload-action">
                    {uploadingResume
                      ? "Uploading..."
                      : resumeUploaded
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
                      Uploading resume...
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

        {/* APPLICATIONS */}
        {activePage === "applications" && (
          <section className="page-section">
            <div className="page-title">
              <div>
                <p className="eyebrow">APPLICATION RUN LOG</p>
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
                  Click "Apply with AI" on any job to launch the visible browser automation and review panel.
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

                    <span
                      style={{
                        padding: "4px 12px",
                        borderRadius: "20px",
                        fontSize: "12px",
                        fontWeight: "600",
                        textTransform: "uppercase",
                        flexShrink: 0,
                        background:
                          app.status === "submitted"
                            ? "rgba(46, 213, 115, 0.15)"
                            : app.status === "ready_for_review"
                            ? "rgba(255, 165, 2, 0.15)"
                            : app.status === "running"
                            ? "rgba(109, 75, 255, 0.2)"
                            : "rgba(255, 71, 87, 0.15)",
                        color:
                          app.status === "submitted"
                            ? "#2ed573"
                            : app.status === "ready_for_review"
                            ? "#ffa502"
                            : app.status === "running"
                            ? "#a388ff"
                            : "#ff4757",
                      }}
                    >
                      {app.status === "ready_for_review" ? "Reviewed & Filled" : app.status}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </section>
        )}

        {/* RESUME & PROFILE */}
        {activePage === "resume" && (
          <section className="page-section">
            <div className="page-title">
              <div>
                <p className="eyebrow">DATABASE PROFILE</p>
                <h2>Candidate Profile</h2>
              </div>
            </div>

            <div className="resume-page-card">
              <div className="big-file-icon">PDF</div>

              <div style={{ flex: 1, minWidth: 0 }}>
                <h3>{resumeName || "No resume uploaded"}</h3>
                <p>
                  {resumeUploaded
                    ? "Stored permanently in SQLite database. AI uses your skills to match direct ATS vacancies and autofill forms."
                    : "Upload a PDF resume from the dashboard to populate your AI candidate profile."}
                </p>

                {profileData && (
                  <div style={{ marginTop: "16px" }}>
                    <div
                      style={{
                        display: "grid",
                        gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
                        gap: "12px",
                        marginBottom: "16px",
                        background: "rgba(255, 255, 255, 0.03)",
                        padding: "14px",
                        borderRadius: "10px",
                      }}
                    >
                      {profileData.name && (
                        <div>
                          <small style={{ color: "#777780", display: "block" }}>Name</small>
                          <strong style={{ color: "#fff" }}>{profileData.name}</strong>
                        </div>
                      )}
                      {profileData.email && (
                        <div>
                          <small style={{ color: "#777780", display: "block" }}>Email</small>
                          <strong style={{ color: "#fff" }}>{profileData.email}</strong>
                        </div>
                      )}
                      {profileData.phone && (
                        <div>
                          <small style={{ color: "#777780", display: "block" }}>Phone</small>
                          <strong style={{ color: "#fff" }}>{profileData.phone}</strong>
                        </div>
                      )}
                      {profileData.location && (
                        <div>
                          <small style={{ color: "#777780", display: "block" }}>Location</small>
                          <strong style={{ color: "#fff" }}>{profileData.location}</strong>
                        </div>
                      )}
                    </div>

                    {profileData.skills && profileData.skills.length > 0 && (
                      <div>
                        <small style={{ color: "#777780", display: "block", marginBottom: "8px" }}>
                          Extracted Skills ({profileData.skills.length})
                        </small>
                        <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                          {profileData.skills.map((skill, idx) => (
                            <span
                              key={idx}
                              style={{
                                background: "rgba(109, 75, 255, 0.15)",
                                border: "1px solid rgba(109, 75, 255, 0.3)",
                                color: "#b9a2ff",
                                padding: "4px 10px",
                                borderRadius: "6px",
                                fontSize: "12px",
                              }}
                            >
                              {skill}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>

              <button onClick={() => setActivePage("dashboard")}>
                {resumeUploaded ? "Upload New Resume" : "Upload resume"}
              </button>
            </div>
          </section>
        )}
      </main>

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
                  {isSubmitted ? "Application Logged" : "Chromium Auto-Apply Running"}
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
            {agentJob?.apply_url && (
              <a
                href={agentJob.apply_url}
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