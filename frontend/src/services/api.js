// src/services/api.js
const API_BASE = "http://127.0.0.1:8000";

export const getSavedJobs = async () => {
  try {
    const response = await fetch(`${API_BASE}/api/jobs`);
    if (!response.ok) return [];
    const data = await response.json();
    return Array.isArray(data) ? data : data.jobs || [];
  } catch (error) {
    console.warn("Could not fetch saved jobs:", error);
    return [];
  }
};

export const getSavedProfile = async () => {
  try {
    const response = await fetch(`${API_BASE}/api/profile`);
    if (!response.ok) return null;
    const data = await response.json();
    return data;
  } catch (error) {
    console.warn("Could not fetch saved profile:", error);
    return null;
  }
};

export const saveCandidateProfile = async (profileData) => {
  const response = await fetch(`${API_BASE}/api/profile`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(profileData),
  });

  if (!response.ok) {
    throw new Error(`Profile save failed: ${response.status}`);
  }

  return await response.json();
};

export const getAgentSettings = async () => {
  try {
    const response = await fetch(`${API_BASE}/api/settings`);
    if (!response.ok) return null;
    const data = await response.json();
    return data.settings;
  } catch (error) {
    console.warn("Could not fetch agent settings:", error);
    return null;
  }
};

export const saveAgentSettings = async (settings) => {
  const response = await fetch(`${API_BASE}/api/settings`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(settings),
  });

  if (!response.ok) {
    throw new Error(`Settings save failed: ${response.status}`);
  }

  return await response.json();
};

export const getApplications = async () => {
  try {
    const response = await fetch(`${API_BASE}/api/applications`);
    if (!response.ok) return [];
    const data = await response.json();
    return data.applications || [];
  } catch (error) {
    console.warn("Could not fetch applications:", error);
    return [];
  }
};

export const getApplicationFields = async (appId) => {
  try {
    const response = await fetch(`${API_BASE}/api/applications/${appId}/fields`);
    if (!response.ok) return [];
    const data = await response.json();
    return data.fields || [];
  } catch (error) {
    console.warn(`Could not fetch fields for application ${appId}:`, error);
    return [];
  }
};

export const clearSavedJobs = async () => {
  const response = await fetch(`${API_BASE}/api/jobs`, {
    method: "DELETE",
  });
  return response.ok;
};

export const searchJobs = async (resumeFile, role, location) => {
  const formData = new FormData();
  
  if (resumeFile) {
    formData.append("resume", resumeFile);
  }
  formData.append("role", role || "");
  formData.append("location", location || "");

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

export const startApplicationAgent = async (job, settings = null) => {
  const response = await fetch(`${API_BASE}/api/apply`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ job, settings }),
  });

  if (!response.ok) {
    throw new Error(`Application failed: ${response.status}`);
  }
  
  return await response.json();
};

export const confirmApplicationSubmit = async (applicationId, jobUrl) => {
  const response = await fetch(`${API_BASE}/api/apply/submit-confirm`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ application_id: applicationId, job_url: jobUrl }),
  });

  if (!response.ok) {
    throw new Error(`Confirmation failed: ${response.status}`);
  }

  return await response.json();
};