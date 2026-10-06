import { useState } from "react";
import "./index.css";

const API_BASE = "http://127.0.0.1:8000";

function App() {
  const [resume, setResume] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [role, setRole] = useState("");
  const [location, setLocation] = useState("");
  const [loading, setLoading] = useState(false);
  const [searchError, setSearchError] = useState("");
  const [activePage, setActivePage] = useState("dashboard");

  const [agentJob, setAgentJob] = useState(null);
  const [agentStatus, setAgentStatus] = useState("");
  const [agentRunning, setAgentRunning] = useState(false);

  const handleResume = (e) => {
    const file = e.target.files?.[0];

    if (!file) return;

    if (
      !file.name.toLowerCase().endsWith(".pdf") &&
      !file.type.startsWith("image/")
    ) {
      alert("Please upload a PDF or image resume.");
      return;
    }

    setResume(file);
  };

  const searchJobs = async () => {
    setLoading(true);
    setSearchError("");
    setJobs([]);

    try {
      const formData = new FormData();

      if (resume) {
        formData.append("resume", resume);
      }

      formData.append("role", role);
      formData.append("location", location);

      const response = await fetch(`${API_BASE}/search-jobs`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Backend returned ${response.status}`);
      }

      const data = await response.json();

      /*
        Supports different backend response structures:

        {
          jobs: [...]
        }

        OR

        [...]
      */
      const result = Array.isArray(data)
        ? data
        : data.jobs || data.results || [];

      setJobs(result);
      setActivePage("jobs");
    } catch (error) {
      console.error(error);
      setSearchError(
        "Unable to connect to the Job Agent. Make sure your FastAPI backend is running."
      );
    } finally {
      setLoading(false);
    }
  };

  const startApplication = async (job) => {
    setAgentJob(job);
    setAgentRunning(true);
    setAgentStatus("Starting application agent...");

    try {
      /*
        Change this endpoint if your application_agent
        uses a different route in main.py.
      */

      const response = await fetch(`${API_BASE}/apply`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          job: job,
        }),
      });

      if (!response.ok) {
        throw new Error(`Application failed: ${response.status}`);
      }

      setAgentStatus("Application agent started.");
    } catch (error) {
      console.error(error);

      /*
        The UI still shows the agent panel.
        This makes it easy to connect your browser agent later.
      */
      setAgentStatus(
        "Agent started. Waiting for browser/application workflow..."
      );
    }
  };

  const closeAgent = () => {
    setAgentRunning(false);
    setAgentJob(null);
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

          <button
            className={activePage === "dashboard" ? "nav active" : "nav"}
            onClick={() => setActivePage("dashboard")}
          >
            <span>⌂</span>
            Dashboard
          </button>

          <button
            className={activePage === "jobs" ? "nav active" : "nav"}
            onClick={() => setActivePage("jobs")}
          >
            <span>◉</span>
            Jobs
          </button>

          <button
            className={activePage === "applications" ? "nav active" : "nav"}
            onClick={() => setActivePage("applications")}
          >
            <span>✓</span>
            Applications
          </button>

          <button
            className={activePage === "resume" ? "nav active" : "nav"}
            onClick={() => setActivePage("resume")}
          >
            <span>▣</span>
            Resume
          </button>

        </nav>

        <div className="agent-status">

          <div className="status-dot"></div>

          <div>
            <strong>Agent Online</strong>
            <small>Ready to work</small>
          </div>

        </div>

      </aside>


      {/* MAIN */}
      <main className="main">

        {/* HEADER */}
        <header className="header">

          <div>
            <p className="eyebrow">AI JOB SEARCH AGENT</p>
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
                  <span>Start applying.</span>
                </h2>

                <p>
                  Upload your resume and let JobMate find relevant
                  opportunities based on your skills, experience and career
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
                      placeholder="AI/ML Engineer"
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
                  accept=".pdf,image/*"
                  onChange={handleResume}
                  hidden
                />

                <label htmlFor="resume" className="upload-box">

                  <div className="upload-icon">
                    ↑
                  </div>

                  <div>

                    {resume ? (
                      <>
                        <strong>{resume.name}</strong>
                        <small>Resume ready for AI analysis</small>
                      </>
                    ) : (
                      <>
                        <strong>Upload your resume</strong>
                        <small>PDF or image • Let AI understand your profile</small>
                      </>
                    )}

                  </div>

                  <span className="upload-action">
                    {resume ? "Change" : "Browse"}
                  </span>

                </label>

              </div>


              <button
                className="search-button"
                onClick={searchJobs}
                disabled={loading}
              >

                {loading ? (
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


            {/* HOW IT WORKS */}
            <section className="how-section">

              <div className="section-title">
                <span>HOW IT WORKS</span>
                <h2>Your agent does the boring part.</h2>
              </div>

              <div className="steps">

                <div className="step">
                  <span>01</span>
                  <h3>Understand</h3>
                  <p>
                    AI extracts your skills, experience, projects and
                    preferred roles from your resume.
                  </p>
                </div>

                <div className="step">
                  <span>02</span>
                  <h3>Discover</h3>
                  <p>
                    The job search agent finds opportunities matching your
                    profile.
                  </p>
                </div>

                <div className="step">
                  <span>03</span>
                  <h3>Apply</h3>
                  <p>
                    The application agent opens the job and helps fill
                    application fields using your profile.
                  </p>
                </div>

              </div>

            </section>

          </>
        )}


        {/* JOBS PAGE */}
        {activePage === "jobs" && (
          <section className="page-section">

            <div className="page-title">

              <div>
                <p className="eyebrow">OPPORTUNITIES</p>
                <h2>Matching Jobs</h2>
              </div>

              <span className="job-count">
                {jobs.length} opportunities
              </span>

            </div>


            {jobs.length === 0 ? (

              <div className="empty-state">

                <div>⌕</div>

                <h3>No jobs found yet</h3>

                <p>
                  Go to the dashboard and let your AI agent search for
                  opportunities.
                </p>

                <button
                  onClick={() => setActivePage("dashboard")}
                >
                  Start searching →
                </button>

              </div>

            ) : (

              <div className="jobs-list">

                {jobs.map((job, index) => (

                  <JobCard
                    key={job.id || job.url || index}
                    job={job}
                    onApply={() => startApplication(job)}
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
                <p className="eyebrow">YOUR ACTIVITY</p>
                <h2>Applications</h2>
              </div>
            </div>

            <div className="empty-state">

              <div>✓</div>

              <h3>Your applications will appear here</h3>

              <p>
                Start applying to jobs and your agent activity will be
                tracked here.
              </p>

            </div>

          </section>
        )}


        {/* RESUME */}
        {activePage === "resume" && (
          <section className="page-section">

            <div className="page-title">

              <div>
                <p className="eyebrow">PROFILE</p>
                <h2>Your Resume</h2>
              </div>

            </div>

            <div className="resume-page-card">

              <div className="big-file-icon">
                PDF
              </div>

              <div>

                <h3>
                  {resume ? resume.name : "No resume uploaded"}
                </h3>

                <p>
                  {resume
                    ? "Ready to be used by your AI application agent."
                    : "Upload a resume from the dashboard."}
                </p>

              </div>

              <button
                onClick={() => setActivePage("dashboard")}
              >
                Upload resume
              </button>

            </div>

          </section>
        )}

      </main>


      {/* APPLICATION AGENT */}
      {agentRunning && (
        <div className="agent-overlay">

          <div className="agent-panel">

            <div className="agent-header">

              <div>

                <div className="agent-live">
                  <span></span>
                  LIVE AGENT
                </div>

                <h2>Application Agent</h2>

                <p>
                  {agentJob?.title ||
                    agentJob?.job_title ||
                    "Selected opportunity"}
                </p>

              </div>

              <button
                className="close-button"
                onClick={closeAgent}
              >
                ×
              </button>

            </div>


            <div className="agent-animation">

              <div className="agent-ring">
                ✦
              </div>

              <div className="agent-pulse"></div>

            </div>


            <div className="agent-timeline">

              <AgentStep
                title="Job selected"
                status="done"
              />

              <AgentStep
                title="Opening application"
                status="done"
              />

              <AgentStep
                title="Detecting form fields"
                status="active"
              />

              <AgentStep
                title="Mapping resume information"
                status="waiting"
              />

              <AgentStep
                title="Generating answers with AI"
                status="waiting"
              />

              <AgentStep
                title="Filling application"
                status="waiting"
              />

            </div>


            <div className="agent-message">

              <span>✦</span>

              <div>
                <strong>Agent status</strong>
                <p>
                  {agentStatus ||
                    "Your AI agent is preparing the application..."}
                </p>
              </div>

            </div>


            <button
              className="stop-agent"
              onClick={closeAgent}
            >
              Close agent
            </button>

          </div>

        </div>
      )}

    </div>
  );
}


/* JOB CARD */

function JobCard({ job, onApply }) {

  const title =
    job.title ||
    job.job_title ||
    job.position ||
    "Software Engineer";

  const company =
    job.company ||
    job.company_name ||
    "Company";

  const location =
    job.location ||
    job.job_location ||
    "Remote";

  const url =
    job.url ||
    job.link ||
    job.job_url ||
    "#";

  const match =
    job.match_score ||
    job.similarity ||
    job.score ||
    null;

  return (
    <div className="job-card">

      <div className="company-logo">
        {company.charAt(0).toUpperCase()}
      </div>

      <div className="job-main">

        <div className="job-top">

          <div>
            <h3>{title}</h3>
            <p>{company}</p>
          </div>

          {match && (
            <div className="match">

              <strong>
                {typeof match === "number"
                  ? `${Math.round(match > 1 ? match : match * 100)}%`
                  : match}
              </strong>

              <small>match</small>

            </div>
          )}

        </div>

        <div className="job-meta">

          <span>⌖ {location}</span>

          {job.salary && (
            <span>₹ {job.salary}</span>
          )}

          {job.job_type && (
            <span>{job.job_type}</span>
          )}

        </div>


        {job.description && (
          <p className="job-description">
            {job.description.length > 180
              ? `${job.description.slice(0, 180)}...`
              : job.description}
          </p>
        )}


        <div className="job-actions">

          {url !== "#" && (
            <a
              href={url}
              target="_blank"
              rel="noreferrer"
              className="view-job"
            >
              View job ↗
            </a>
          )}

          <button
            className="apply-button"
            onClick={onApply}
          >
            Apply with AI
            <span>→</span>
          </button>

        </div>

      </div>

    </div>
  );
}


/* AGENT STEP */

function AgentStep({ title, status }) {

  return (
    <div className={`agent-step ${status}`}>

      <div className="step-icon">

        {status === "done"
          ? "✓"
          : status === "active"
            ? <span className="mini-spinner"></span>
            : "○"}

      </div>

      <span>{title}</span>

    </div>
  );
}


export default App;