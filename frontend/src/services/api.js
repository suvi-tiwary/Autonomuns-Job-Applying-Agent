// src/services/api.js
const API_BASE = "http://127.0.0.1:8000";

export const searchJobs = async (resumeFile, role, location) => {
  const formData = new FormData();
  
  if (resumeFile) {
    formData.append("resume", resumeFile);
  }
  formData.append("role", role);
  formData.append("location", location);

  const response = await fetch(`${API_BASE}/api/jobs/search`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    let errorMessage = `Backend returned ${response.status}`;
    try {
      const errorData = await response.json();
      if (errorData.detail) {
        if (Array.isArray(errorData.detail)) {
          errorMessage = errorData.detail
            .map((err) => `${err.loc.join(".")} - ${err.msg}`)
            .join(", ");
        } else {
          errorMessage = errorData.detail;
        }
      }
    } catch (e) {
      console.error("Failed to parse error response", e);
    }
    throw new Error(errorMessage);
  }

  const data = await response.json();
  return Array.isArray(data) ? data : data.jobs || data.results || [];
};

export const startApplicationAgent = async (job) => {
  const response = await fetch(`${API_BASE}/apply`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ job }),
  });

  if (!response.ok) {
    throw new Error(`Application failed: ${response.status}`);
  }
  
  return await response.json();
};