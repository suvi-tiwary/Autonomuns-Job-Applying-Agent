// src/App.jsx

import { useState } from "react";
import { searchJobs, startApplicationAgent } from "./services/api";
import JobCard from "./components/JobCard";
import "./index.css";

const API_BASE = "http://127.0.0.1:8000";

function App() {
  const [resume, setResume] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [role, setRole] = useState("");
  const [location, setLocation] = useState("");

  const [loading, setLoading] = useState(false);
  const [uploadingResume, setUploadingResume] = useState(false);

  const [resumeUploaded, setResumeUploaded] = useState(false);
  const [searchError, setSearchError] = useState("");

  const [activePage, setActivePage] = useState("dashboard");

  const [agentJob, setAgentJob] = useState(null);
  const [agentStatus, setAgentStatus] = useState("");
  const [agentRunning, setAgentRunning] = useState(false);

  /*
  ============================================================
  RESUME UPLOAD
  ============================================================
  */

  const handleResume = async (e) => {
    const file = e.target.files?.[0];

    if (!file) {
      return;
    }

    // Current FastAPI backend supports PDF resumes.
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      alert("Please upload a PDF resume.");
      e.target.value = "";
      return;
    }

    // Show selected file immediately.
    setResume(file);

    // Reset previous state.
    setResumeUploaded(false);
    setSearchError("");
    setUploadingResume(true);

    try {
      const formData = new FormData();

      /*
        IMPORTANT:

        Backend route:

        POST /api/resume/upload

        Backend expects:

        file: UploadFile = File(...)

        Therefore the FormData field MUST be "file".
      */
      formData.append("file", file);

      const response = await fetch(
        `${API_BASE}/api/resume/upload`,
        {
          method: "POST",
          body: formData,
        }
      );

      let data = {};

      try {
        data = await response.json();
      } catch {
        data = {};
      }

      if (!response.ok) {
        throw new Error(
          data.detail ||
            `Resume upload failed with status ${response.status}`
        );
      }

      /*
        At this point FastAPI has:

        1. Saved the PDF
        2. Extracted the resume text
        3. Structured the resume
        4. Stored current_profile

        Therefore /api/jobs/search can now run.
      */
      setResumeUploaded(true);

      console.log("Resume uploaded successfully:", data);
    } catch (error) {
      console.error("Resume upload failed:", error);

      setResumeUploaded(false);

      setSearchError(
        error.message || "Unable to upload your resume."
      );
    } finally {
      setUploadingResume(false);
    }
  };

  /*
  ============================================================
  SEARCH JOBS
  ============================================================
  */

  const handleSearch = async () => {
    // No file selected.
    if (!resume) {
      setSearchError(
        "Please upload your resume before searching."
      );
      return;
    }

    // File selected but backend upload hasn't succeeded.
    if (!resumeUploaded) {
      setSearchError(
        "Please wait for the resume upload to finish before searching."
      );
      return;
    }

    setLoading(true);
    setSearchError("");
    setJobs([]);

    try {
      /*
        The resume has already been uploaded to:

        POST /api/resume/upload

        So the backend already has current_profile.

        searchJobs can now call:

        POST /api/jobs/search
      */
      const result = await searchJobs(
        resume,
        role,
        location
      );

      setJobs(result);
      setActivePage("jobs");
    } catch (error) {
      console.error("Search failed:", error);

      setSearchError(
        error.message ||
          "Unable to search for jobs."
      );
    } finally {
      setLoading(false);
    }
  };

  /*
  ============================================================
  APPLICATION AGENT
  ============================================================
  */

  const handleApply = async (job) => {
    setAgentJob(job);
    setAgentRunning(true);
    setAgentStatus(
      "Starting application agent..."
    );

    try {
      await startApplicationAgent(job);

      setAgentStatus(
        "Application agent started successfully."
      );
    } catch (error) {
      console.error(
        "Agent failed:",
        error
      );

      setAgentStatus(
        "Agent started. Waiting for browser/application workflow..."
      );
    }
  };

  /*
  ============================================================
  UI
  ============================================================
  */

  return (
    <div className="app">

      {/* SIDEBAR */}

      <aside className="sidebar">

        <div className="brand">

          <div className="brand-icon">
            ✦
          </div>

          <div>
            <h2>JobMate</h2>
            <span>AI Career Agent</span>
          </div>

        </div>

        <nav>

          {[
            "dashboard",
            "jobs",
            "applications",
            "resume",
          ].map((page) => (

            <button
              key={page}
              className={`nav ${
                activePage === page
                  ? "active"
                  : ""
              }`}
              onClick={() =>
                setActivePage(page)
              }
            >

              <span>
                {page === "dashboard"
                  ? "⌂"
                  : page === "jobs"
                  ? "◉"
                  : page === "applications"
                  ? "✓"
                  : "▣"}
              </span>

              {page.charAt(0).toUpperCase() +
                page.slice(1)}

            </button>

          ))}

        </nav>

        <div className="agent-status">

          <div className="status-dot"></div>

          <div>
            <strong>
              Agent Online
            </strong>

            <small>
              Ready to work
            </small>
          </div>

        </div>

      </aside>


      {/* MAIN CONTENT */}

      <main className="main">

        <header className="header">

          <div>

            <p className="eyebrow">
              AI JOB SEARCH AGENT
            </p>

            <h1>
              Find your next
              <span> opportunity.</span>
            </h1>

          </div>

          <div className="header-right">

            <div className="online">

              <span></span>

              Backend connected

            </div>

          </div>

        </header>


        {/* DASHBOARD */}

        {activePage === "dashboard" && (

          <>

            <section className="hero">

              <div className="hero-content">

                <div className="hero-badge">
                  ✦ Your AI job hunting assistant
                </div>

                <h2>
                  Stop searching.
                  <br />
                  <span>
                    Start applying.
                  </span>
                </h2>

                <p>
                  Upload your resume and let
                  JobMate find relevant
                  opportunities based on your
                  skills, experience and career
                  goals.
                </p>

              </div>

              <div className="hero-orb">

                <div className="orb-inner">
                  ✦
                </div>

              </div>

            </section>


            {/* SEARCH CARD */}

            <section className="search-card">

              <div className="section-heading">

                <div>

                  <span className="number">
                    01
                  </span>

                  <h3>
                    Tell your agent what you're
                    looking for
                  </h3>

                </div>

              </div>


              <div className="form-grid">

                <div className="input-group">

                  <label>
                    Target role
                  </label>

                  <div className="input-wrapper">

                    <span>
                      ⌕
                    </span>

                    <input
                      value={role}
                      onChange={(e) =>
                        setRole(e.target.value)
                      }
                      placeholder="AI/ML Engineer"
                    />

                  </div>

                </div>


                <div className="input-group">

                  <label>
                    Location
                  </label>

                  <div className="input-wrapper">

                    <span>
                      ⌖
                    </span>

                    <input
                      value={location}
                      onChange={(e) =>
                        setLocation(e.target.value)
                      }
                      placeholder="Bengaluru, Remote..."
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

                <label
                  htmlFor="resume"
                  className="upload-box"
                >

                  <div className="upload-icon">
                    ↑
                  </div>

                  <div>

                    {resume ? (

                      <>

                        <strong>
                          {resume.name}
                        </strong>

                        <small>

                          {uploadingResume
                            ? "Uploading resume to AI agent..."
                            : resumeUploaded
                            ? "Resume uploaded and ready for AI analysis"
                            : "Resume upload failed"}

                        </small>

                      </>

                    ) : (

                      <>

                        <strong>
                          Upload your resume
                        </strong>

                        <small>
                          PDF • Let AI understand
                          your profile
                        </small>

                      </>

                    )}

                  </div>

                  <span className="upload-action">

                    {uploadingResume
                      ? "Uploading..."
                      : resume
                      ? "Change"
                      : "Browse"}

                  </span>

                </label>

              </div>


              {/* SEARCH BUTTON */}

              <button
                className="search-button"
                onClick={handleSearch}
                disabled={
                  loading ||
                  uploadingResume
                }
              >

                {uploadingResume ? (

                  <>
                    <span className="spinner"></span>
                    Uploading resume...
                  </>

                ) : loading ? (

                  <>
                    <span className="spinner"></span>
                    Agent is searching...
                  </>

                ) : (

                  <>
                    Find matching jobs
                    <span>→</span>
                  </>

                )}

              </button>


              {searchError && (

                <div className="error-box">

                  ⚠ {searchError}

                </div>

              )}

            </section>

          </>

        )}


        {/* JOBS PAGE */}

        {activePage === "jobs" && (

          <section className="page-section">

            <div className="page-title">

              <div>

                <p className="eyebrow">
                  OPPORTUNITIES
                </p>

                <h2>
                  Matching Jobs
                </h2>

              </div>

              <span className="job-count">
                {jobs.length} opportunities
              </span>

            </div>


            {jobs.length === 0 ? (

              <div className="empty-state">

                <div>⌕</div>

                <h3>
                  No jobs found yet
                </h3>

                <p>
                  Go to the dashboard and let
                  your AI agent search for
                  opportunities.
                </p>

                <button
                  onClick={() =>
                    setActivePage("dashboard")
                  }
                >
                  Start searching →
                </button>

              </div>

            ) : (

              <div className="jobs-list">

                {jobs.map(
                  (job, index) => (

                    <JobCard
                      key={
                        job.id ||
                        job.url ||
                        index
                      }
                      job={job}
                      onApply={() =>
                        handleApply(job)
                      }
                    />

                  )
                )}

              </div>

            )}

          </section>

        )}


        {/* APPLICATIONS */}

        {activePage === "applications" && (

          <section className="page-section">

            <div className="page-title">

              <h2>
                Applications
              </h2>

            </div>

            <div className="empty-state">

              <div>
                ✓
              </div>

              <h3>
                Your applications will
                appear here
              </h3>

            </div>

          </section>

        )}


        {/* RESUME */}

        {activePage === "resume" && (

          <section className="page-section">

            <div className="page-title">

              <h2>
                Your Resume
              </h2>

            </div>

            <div className="resume-page-card">

              <div className="big-file-icon">
                PDF
              </div>

              <div>

                <h3>
                  {resume
                    ? resume.name
                    : "No resume uploaded"}
                </h3>

                <p>

                  {resume
                    ? resumeUploaded
                      ? "Uploaded and ready for your AI application agent."
                      : "Resume selected but not uploaded yet."
                    : "Upload a resume from the dashboard."}

                </p>

              </div>

              <button
                onClick={() =>
                  setActivePage("dashboard")
                }
              >
                Upload resume
              </button>

            </div>

          </section>

        )}

      </main>


      {/* APPLICATION AGENT OVERLAY */}

      {agentRunning && (

        <div className="agent-overlay">

          <div className="agent-panel">

            <div className="agent-header">

              <div>

                <div className="agent-live">

                  <span></span>
                  LIVE AGENT

                </div>

                <h2>
                  Application Agent
                </h2>

                <p>
                  {agentJob?.title ||
                    agentJob?.job_title ||
                    "Selected opportunity"}
                </p>

              </div>

              <button
                className="close-button"
                onClick={() =>
                  setAgentRunning(false)
                }
              >
                ×
              </button>

            </div>


            <div className="agent-message">

              <span>
                ✦
              </span>

              <div>

                <strong>
                  Agent status
                </strong>

                <p>
                  {agentStatus ||
                    "Your AI agent is preparing the application..."}
                </p>

              </div>

            </div>


            <button
              className="stop-agent"
              onClick={() =>
                setAgentRunning(false)
              }
            >
              Close agent
            </button>

          </div>

        </div>

      )}

    </div>
  );
}

export default App;