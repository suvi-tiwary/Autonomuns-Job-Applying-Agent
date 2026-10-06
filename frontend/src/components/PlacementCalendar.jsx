// src/components/PlacementCalendar.jsx

import React, { useState } from "react";
import {
  PLATFORMS_DATA,
  COMPANIES_DATA,
  HIRING_CALENDAR,
  OUTREACH_TEMPLATES,
} from "../data/placementData";

export default function PlacementCalendar({ onApplyWithAgent }) {
  const [activeTab, setActiveTab] = useState("companies");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [selectedPriority, setSelectedPriority] = useState("All");
  const [copiedIndex, setCopiedIndex] = useState(null);

  // Interactive Checklist State
  const [checklist, setChecklist] = useState({
    gradYear: false,
    intlEligible: false,
    workAuth: false,
    visaSponsorship: false,
    remoteWorldwide: false,
    techStackMatch: false,
  });

  const categories = [
    "All",
    "FAANG / Big Tech",
    "HFT / Quant",
    "Frontier AI & GenAI",
    "European Product & Tech",
    "Cloud, Infra & DevTools",
    "100% Remote / Distributed",
    "High-Growth Startups & YC",
    "APAC / Japan / Singapore",
  ];

  const priorities = ["All", "🔴 Dream", "🟠 High Value", "🟢 Opportunity"];

  // Filtered Companies
  const filteredCompanies = COMPANIES_DATA.filter((company) => {
    const matchesSearch =
      company.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      company.focus.toLowerCase().includes(searchQuery.toLowerCase()) ||
      company.region.toLowerCase().includes(searchQuery.toLowerCase()) ||
      company.tags.some((tag) =>
        tag.toLowerCase().includes(searchQuery.toLowerCase())
      );

    const matchesCategory =
      selectedCategory === "All" || company.category === selectedCategory;

    const matchesPriority =
      selectedPriority === "All" ||
      (selectedPriority === "🔴 Dream" && company.priority === "Dream") ||
      (selectedPriority === "🟠 High Value" && company.priority === "High Value") ||
      (selectedPriority === "🟢 Opportunity" && company.priority === "Opportunity");

    return matchesSearch && matchesCategory && matchesPriority;
  });

  const handleCopyTemplate = (text, idx) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(idx);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const toggleChecklistItem = (key) => {
    setChecklist((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const checkedCount = Object.values(checklist).filter(Boolean).length;

  return (
    <div className="placement-hub" style={{ width: "100%", maxWidth: "100%", minWidth: 0 }}>
      {/* HEADER */}
      <div className="page-title" style={{ marginBottom: "20px", flexWrap: "wrap", gap: "12px" }}>
        <div style={{ minWidth: 0, flex: 1 }}>
          <p className="eyebrow">GLOBAL OPPORTUNITY RADAR</p>
          <h2 style={{ wordBreak: "break-word" }}>International Placement & Target Directory</h2>
        </div>
        <div style={{ display: "flex", gap: "8px", flexShrink: 0 }}>
          <span className="job-count" style={{ background: "rgba(109, 75, 255, 0.15)", color: "#a388ff", padding: "6px 12px", borderRadius: "20px" }}>
            {COMPANIES_DATA.length}+ Targets Verified
          </span>
        </div>
      </div>

      {/* TOP NAVIGATION TABS */}
      <div
        style={{
          display: "flex",
          gap: "8px",
          borderBottom: "1px solid #1c1c22",
          paddingBottom: "12px",
          marginBottom: "24px",
          overflowX: "auto",
          maxWidth: "100%",
        }}
      >
        {[
          { id: "companies", label: `🏢 Targets (${COMPANIES_DATA.length})` },
          { id: "platforms", label: `🌐 Platforms (${PLATFORMS_DATA.length})` },
          { id: "calendar", label: "🗓️ Seasons Calendar" },
          { id: "outreach", label: "✍️ Cold Outreach" },
          { id: "eligibility", label: `⚠️ 6-Step Check (${checkedCount}/6)` },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: "8px 14px",
              borderRadius: "10px",
              border: "1px solid",
              borderColor: activeTab === tab.id ? "#8d6bff" : "#24242b",
              background: activeTab === tab.id ? "#19171f" : "#111116",
              color: activeTab === tab.id ? "#fff" : "#85858d",
              fontSize: "13px",
              fontWeight: "600",
              cursor: "pointer",
              whiteSpace: "nowrap",
              flexShrink: 0,
              transition: "0.2s ease",
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* TAB 1: COMPANIES DIRECTORY */}
      {activeTab === "companies" && (
        <div>
          {/* SEARCH & FILTERS */}
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "14px",
              background: "#111116",
              border: "1px solid #24242b",
              borderRadius: "14px",
              padding: "16px 20px",
              marginBottom: "24px",
              maxWidth: "100%",
            }}
          >
            <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
              <div style={{ flex: 1, minWidth: "240px", position: "relative" }}>
                <input
                  type="text"
                  placeholder="Search by company name, tech (C++, PyTorch, RAG), or location..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  style={{
                    width: "100%",
                    boxSizing: "border-box",
                    padding: "10px 14px",
                    background: "#0d0d12",
                    border: "1px solid #282832",
                    borderRadius: "10px",
                    color: "#fff",
                    fontSize: "14px",
                    outline: "none",
                  }}
                />
              </div>

              {/* PRIORITY FILTER */}
              <div style={{ display: "flex", gap: "6px", alignItems: "center", flexWrap: "wrap" }}>
                <span style={{ fontSize: "12px", color: "#777780", marginRight: "4px" }}>Priority:</span>
                {priorities.map((p) => (
                  <button
                    key={p}
                    onClick={() => setSelectedPriority(p)}
                    style={{
                      padding: "6px 12px",
                      borderRadius: "8px",
                      border: "1px solid",
                      borderColor: selectedPriority === p ? "#8d6bff" : "rgba(255, 255, 255, 0.08)",
                      background: selectedPriority === p ? "rgba(109, 75, 255, 0.2)" : "transparent",
                      color: selectedPriority === p ? "#fff" : "#a0a0ab",
                      fontSize: "12px",
                      cursor: "pointer",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>

            {/* CATEGORY PILLS */}
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", overflowX: "auto", paddingBottom: "4px" }}>
              {categories.map((cat) => (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  style={{
                    padding: "6px 12px",
                    borderRadius: "20px",
                    border: "1px solid",
                    borderColor: selectedCategory === cat ? "#8d6bff" : "#1f1f26",
                    background: selectedCategory === cat ? "#8d6bff" : "rgba(255, 255, 255, 0.03)",
                    color: selectedCategory === cat ? "#fff" : "#85858d",
                    fontSize: "12px",
                    cursor: "pointer",
                    whiteSpace: "nowrap",
                    transition: "all 0.15s",
                  }}
                >
                  {cat}
                </button>
              ))}
            </div>
          </div>

          {/* COMPANIES GRID */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 320px), 1fr))",
              gap: "18px",
              width: "100%",
            }}
          >
            {filteredCompanies.map((company, idx) => (
              <div
                key={idx}
                style={{
                  background: "#111116",
                  border: "1px solid #202028",
                  borderRadius: "14px",
                  padding: "18px 20px",
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                  minWidth: 0,
                  boxSizing: "border-box",
                }}
              >
                <div style={{ minWidth: 0 }}>
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "flex-start",
                      marginBottom: "10px",
                      flexWrap: "wrap",
                      gap: "6px",
                    }}
                  >
                    <div style={{ minWidth: 0, flex: 1 }}>
                      <h3 style={{ margin: "0 0 4px 0", fontSize: "17px", color: "#fff", wordBreak: "break-word" }}>
                        {company.name}
                      </h3>
                      <span
                        style={{
                          fontSize: "12px",
                          color: "#7e57ff",
                          fontWeight: "500",
                          wordBreak: "break-word",
                        }}
                      >
                        {company.category}
                      </span>
                    </div>

                    <span
                      style={{
                        padding: "3px 8px",
                        borderRadius: "12px",
                        fontSize: "11px",
                        fontWeight: "600",
                        flexShrink: 0,
                        background:
                          company.priority === "Dream"
                            ? "rgba(255, 71, 87, 0.15)"
                            : company.priority === "High Value"
                            ? "rgba(255, 165, 2, 0.15)"
                            : "rgba(46, 213, 115, 0.15)",
                        color:
                          company.priority === "Dream"
                            ? "#ff4757"
                            : company.priority === "High Value"
                            ? "#ffa502"
                            : "#2ed573",
                      }}
                    >
                      {company.priorityLevel} {company.priority}
                    </span>
                  </div>

                  <div style={{ fontSize: "13px", color: "#a0a0ab", marginBottom: "12px", lineHeight: "1.4", wordBreak: "break-word" }}>
                    📍 <strong>{company.region}</strong>
                  </div>

                  <p
                    style={{
                      fontSize: "13px",
                      color: "#c0c0ca",
                      margin: "0 0 12px 0",
                      lineHeight: "1.45",
                      wordBreak: "break-word",
                      overflowWrap: "break-word",
                    }}
                  >
                    {company.focus}
                  </p>

                  <div
                    style={{
                      fontSize: "12px",
                      color: "#85858d",
                      marginBottom: "14px",
                      background: "rgba(255, 255, 255, 0.02)",
                      padding: "6px 10px",
                      borderRadius: "6px",
                      wordBreak: "break-word",
                    }}
                  >
                    🕒 <strong>Hiring:</strong> {company.hiringWindow}
                  </div>

                  {/* TAGS */}
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "5px", marginBottom: "16px" }}>
                    {company.tags.map((tag, tIdx) => (
                      <span
                        key={tIdx}
                        style={{
                          background: "rgba(255, 255, 255, 0.04)",
                          border: "1px solid rgba(255, 255, 255, 0.08)",
                          color: "#9b9ba6",
                          padding: "2px 8px",
                          borderRadius: "6px",
                          fontSize: "11px",
                          wordBreak: "break-word",
                        }}
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>

                {/* ACTION BUTTONS */}
                <div style={{ display: "flex", gap: "8px", borderTop: "1px solid #1c1c24", paddingTop: "14px", flexWrap: "wrap" }}>
                  <a
                    href={company.url}
                    target="_blank"
                    rel="noreferrer"
                    style={{
                      flex: 1,
                      minWidth: "110px",
                      textAlign: "center",
                      padding: "8px 12px",
                      borderRadius: "8px",
                      background: "rgba(255, 255, 255, 0.06)",
                      border: "1px solid rgba(255, 255, 255, 0.12)",
                      color: "#fff",
                      fontSize: "12px",
                      fontWeight: "600",
                      textDecoration: "none",
                      boxSizing: "border-box",
                    }}
                  >
                    Portal ↗
                  </a>

                  <button
                    onClick={() =>
                      onApplyWithAgent({
                        title: `SWE / AI Intern at ${company.name}`,
                        company: company.name,
                        url: company.url,
                        location: company.region,
                      })
                    }
                    style={{
                      flex: 1,
                      minWidth: "110px",
                      padding: "8px 12px",
                      borderRadius: "8px",
                      background: "linear-gradient(135deg, #8d6bff, #6240ff)",
                      border: "none",
                      color: "#fff",
                      fontSize: "12px",
                      fontWeight: "600",
                      cursor: "pointer",
                      display: "flex",
                      justifyContent: "center",
                      alignItems: "center",
                      gap: "4px",
                      boxSizing: "border-box",
                    }}
                  >
                    <span>✦</span> AI Apply
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 2: INTERNSHIP PLATFORMS */}
      {activeTab === "platforms" && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 320px), 1fr))",
            gap: "18px",
            width: "100%",
          }}
        >
          {PLATFORMS_DATA.map((platform) => (
            <div
              key={platform.id}
              style={{
                background: "#111116",
                border: "1px solid #24242b",
                borderRadius: "14px",
                padding: "20px",
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
                minWidth: 0,
                boxSizing: "border-box",
              }}
            >
              <div style={{ minWidth: 0 }}>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginBottom: "12px",
                    flexWrap: "wrap",
                    gap: "8px",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "10px", minWidth: 0 }}>
                    <span style={{ fontSize: "24px", flexShrink: 0 }}>{platform.icon}</span>
                    <h3 style={{ margin: 0, fontSize: "17px", color: "#fff", wordBreak: "break-word" }}>
                      {platform.name}
                    </h3>
                  </div>
                  <span
                    style={{
                      background: "rgba(109, 75, 255, 0.15)",
                      color: "#a388ff",
                      fontSize: "11px",
                      fontWeight: "600",
                      padding: "3px 8px",
                      borderRadius: "6px",
                      flexShrink: 0,
                    }}
                  >
                    {platform.badge}
                  </span>
                </div>

                <p style={{ fontSize: "13px", color: "#c0c0ca", lineHeight: "1.45", margin: "0 0 14px 0", wordBreak: "break-word" }}>
                  {platform.description}
                </p>

                <div
                  style={{
                    background: "rgba(255, 255, 255, 0.03)",
                    border: "1px solid rgba(255, 255, 255, 0.06)",
                    borderRadius: "8px",
                    padding: "10px 12px",
                    fontSize: "12px",
                    color: "#9e9ea7",
                    marginBottom: "16px",
                    wordBreak: "break-word",
                  }}
                >
                  💡 <strong>Pro Tip:</strong> {platform.tips}
                </div>
              </div>

              <a
                href={platform.url}
                target="_blank"
                rel="noreferrer"
                style={{
                  display: "block",
                  textAlign: "center",
                  padding: "10px 16px",
                  borderRadius: "8px",
                  background: "linear-gradient(135deg, #8d6bff, #6240ff)",
                  color: "#fff",
                  fontSize: "13px",
                  fontWeight: "600",
                  textDecoration: "none",
                  boxSizing: "border-box",
                }}
              >
                Launch Platform ↗
              </a>
            </div>
          ))}
        </div>
      )}

      {/* TAB 3: HIRING CALENDAR SEASONS */}
      {activeTab === "calendar" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "16px", width: "100%" }}>
          {HIRING_CALENDAR.map((phase, idx) => (
            <div
              key={idx}
              style={{
                background: "#111116",
                border: "1px solid #24242b",
                borderRadius: "14px",
                padding: "20px 22px",
                borderLeft: "4px solid #8d6bff",
                minWidth: 0,
                boxSizing: "border-box",
              }}
            >
              <span
                style={{
                  fontSize: "12px",
                  color: "#8d6bff",
                  fontWeight: "700",
                  textTransform: "uppercase",
                  letterSpacing: "0.5px",
                  display: "block",
                  marginBottom: "6px",
                  wordBreak: "break-word",
                }}
              >
                {phase.phase}
              </span>

              <h3 style={{ margin: "0 0 8px 0", fontSize: "18px", color: "#fff", wordBreak: "break-word" }}>
                {phase.title}
              </h3>

              <p style={{ margin: "0 0 14px 0", fontSize: "14px", color: "#b0b0bc", lineHeight: "1.5", wordBreak: "break-word" }}>
                {phase.description}
              </p>

              <div
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: "8px",
                  alignItems: "center",
                  marginBottom: "14px",
                }}
              >
                <span style={{ fontSize: "12px", color: "#777780" }}>Key Targets:</span>
                {phase.targets.map((t, tIdx) => (
                  <span
                    key={tIdx}
                    style={{
                      background: "rgba(109, 75, 255, 0.12)",
                      border: "1px solid rgba(109, 75, 255, 0.25)",
                      color: "#b9a2ff",
                      padding: "3px 10px",
                      borderRadius: "6px",
                      fontSize: "12px",
                    }}
                  >
                    {t}
                  </span>
                ))}
              </div>

              <div
                style={{
                  background: "rgba(255, 255, 255, 0.03)",
                  borderLeft: "3px solid #2ed573",
                  padding: "10px 14px",
                  borderRadius: "0 8px 8px 0",
                  fontSize: "13px",
                  color: "#d0d0d8",
                  wordBreak: "break-word",
                }}
              >
                🎯 <strong>Recommended Action:</strong> {phase.action}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* TAB 4: COLD OUTREACH & REFERRALS */}
      {activeTab === "outreach" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "20px", width: "100%" }}>
          <div
            style={{
              background: "rgba(109, 75, 255, 0.08)",
              border: "1px solid rgba(109, 75, 255, 0.2)",
              borderRadius: "12px",
              padding: "16px 20px",
              fontSize: "14px",
              color: "#c0b4ff",
              lineHeight: "1.5",
              wordBreak: "break-word",
            }}
          >
            💡 <strong>Referral Strategy:</strong> Never open with "Can you refer me?".
            First establish connection, demonstrate deployed work, and cite the exact Job ID with tailored technical alignment.
          </div>

          {OUTREACH_TEMPLATES.map((tpl, idx) => (
            <div
              key={idx}
              style={{
                background: "#111116",
                border: "1px solid #24242b",
                borderRadius: "14px",
                padding: "20px",
                minWidth: 0,
                boxSizing: "border-box",
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: "12px",
                  flexWrap: "wrap",
                  gap: "10px",
                }}
              >
                <h4 style={{ margin: 0, fontSize: "16px", color: "#fff", wordBreak: "break-word" }}>
                  {tpl.title}
                </h4>

                <button
                  onClick={() => handleCopyTemplate(tpl.text, idx)}
                  style={{
                    padding: "6px 14px",
                    borderRadius: "8px",
                    background: copiedIndex === idx ? "#2ed573" : "#8d6bff",
                    border: "none",
                    color: "#fff",
                    fontSize: "12px",
                    fontWeight: "600",
                    cursor: "pointer",
                    transition: "all 0.2s",
                    flexShrink: 0,
                  }}
                >
                  {copiedIndex === idx ? "✓ Copied" : "Copy Template"}
                </button>
              </div>

              <div
                style={{
                  background: "#0c0c10",
                  border: "1px solid #1f1f28",
                  borderRadius: "8px",
                  padding: "14px",
                  fontSize: "13px",
                  color: "#d0d0dc",
                  fontFamily: "monospace",
                  whiteSpace: "pre-wrap",
                  lineHeight: "1.5",
                  wordBreak: "break-word",
                  overflowWrap: "anywhere",
                }}
              >
                {tpl.text}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* TAB 5: ELIGIBILITY CHECKLIST */}
      {activeTab === "eligibility" && (
        <div
          style={{
            background: "#111116",
            border: "1px solid #24242b",
            borderRadius: "14px",
            padding: "24px",
            minWidth: 0,
            boxSizing: "border-box",
            width: "100%",
          }}
        >
          <div style={{ marginBottom: "20px" }}>
            <h3 style={{ margin: "0 0 6px 0", fontSize: "18px", color: "#fff", wordBreak: "break-word" }}>
              International Application 6-Rule Validator
            </h3>
            <p style={{ margin: 0, fontSize: "13px", color: "#85858d", wordBreak: "break-word" }}>
              Before applying to international postings, verify these criteria to prevent visa rejections and optimize your acceptance rate.
            </p>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginBottom: "24px" }}>
            {[
              {
                key: "gradYear",
                label: "Target Graduation Year Match",
                desc: "Internships often require graduation in 2025, 2026, or 2027.",
              },
              {
                key: "intlEligible",
                label: "International Applicants Accepted",
                desc: "Check if the company accepts applications outside their home base.",
              },
              {
                key: "workAuth",
                label: "Work Authorization & Pre-requisites",
                desc: "Confirm whether existing work permit or right to work is mandatory.",
              },
              {
                key: "visaSponsorship",
                label: "Visa Sponsorship Provided",
                desc: "Verify if employer sponsors J-1, Tier-2, EU Blue Card, or local work visa.",
              },
              {
                key: "remoteWorldwide",
                label: "True Remote Worldwide Policy",
                desc: "Check if 'Remote' includes India (e.g. Automattic, GitLab, Canonical).",
              },
              {
                key: "techStackMatch",
                label: "Core Stack & Project Fit (C++ / DSA / GenAI / Agents)",
                desc: "Ensure you have at least 1 deployed project addressing their core domain.",
              },
            ].map((item) => (
              <div
                key={item.key}
                onClick={() => toggleChecklistItem(item.key)}
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  gap: "14px",
                  background: checklist[item.key] ? "rgba(46, 213, 115, 0.08)" : "#0c0c10",
                  border: "1px solid",
                  borderColor: checklist[item.key] ? "rgba(46, 213, 115, 0.3)" : "#202028",
                  borderRadius: "10px",
                  padding: "14px 18px",
                  cursor: "pointer",
                  minWidth: 0,
                  boxSizing: "border-box",
                  transition: "all 0.15s ease",
                }}
              >
                <div
                  style={{
                    width: "20px",
                    height: "20px",
                    borderRadius: "6px",
                    border: "2px solid",
                    borderColor: checklist[item.key] ? "#2ed573" : "#555",
                    background: checklist[item.key] ? "#2ed573" : "transparent",
                    display: "grid",
                    placeItems: "center",
                    color: "#000",
                    fontWeight: "bold",
                    fontSize: "12px",
                    marginTop: "2px",
                    flexShrink: 0,
                  }}
                >
                  {checklist[item.key] ? "✓" : ""}
                </div>

                <div style={{ minWidth: 0, flex: 1 }}>
                  <strong style={{ color: checklist[item.key] ? "#2ed573" : "#fff", fontSize: "14px", wordBreak: "break-word" }}>
                    {item.label}
                  </strong>
                  <p style={{ margin: "4px 0 0 0", fontSize: "12px", color: "#85858d", wordBreak: "break-word" }}>
                    {item.desc}
                  </p>
                </div>
              </div>
            ))}
          </div>

          <div
            style={{
              padding: "16px 20px",
              borderRadius: "10px",
              background:
                checkedCount >= 5
                  ? "rgba(46, 213, 115, 0.15)"
                  : checkedCount >= 3
                  ? "rgba(255, 165, 2, 0.15)"
                  : "rgba(255, 71, 87, 0.15)",
              color:
                checkedCount >= 5 ? "#2ed573" : checkedCount >= 3 ? "#ffa502" : "#ff4757",
              fontWeight: "600",
              fontSize: "14px",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              flexWrap: "wrap",
              gap: "10px",
            }}
          >
            <span>
              {checkedCount >= 5
                ? "🟢 High Probability Target - Excellent Eligibility Fit!"
                : checkedCount >= 3
                ? "🟠 Medium Target - Verify visa or remote restrictions before applying."
                : "🔴 Low Match - Role may require local work authorization."}
            </span>
            <span>{checkedCount} of 6 Passed</span>
          </div>
        </div>
      )}
    </div>
  );
}
