// src/data/placementData.js

export const PLATFORMS_DATA = [
  {
    id: "linkedin-jobs",
    name: "LinkedIn Jobs",
    category: "General / Global",
    url: "https://www.linkedin.com/jobs/",
    description: "Primary network for direct applications, recruiter outreach, and alumni referral scouting.",
    badge: "Essential",
    icon: "💼",
    tips: "Search exact query: 'Software Engineer' 'NVIDIA' or 'AI Engineer' 'Mistral' to find active hiring managers."
  },
  {
    id: "wellfound",
    name: "Wellfound (AngelList Talent)",
    category: "Startups & AI",
    url: "https://wellfound.com/jobs",
    description: "Premier marketplace for US & global AI startups, remote engineering roles, and seed to Series-B teams.",
    badge: "Top for Startups",
    icon: "🚀",
    tips: "Filter by 'Remote: Worldwide' or 'Offers Visa Sponsorship' for international openings."
  },
  {
    id: "yc-jobs",
    name: "Y Combinator Work At A Startup",
    category: "YC Startups",
    url: "https://www.workatastartup.com/",
    description: "Direct access to 1,000+ YC funded companies hiring founding engineers, SWE interns, and AI specialists.",
    badge: "High Response Rate",
    icon: "🟧",
    tips: "Founders read applications directly. Attach deployed GitHub project links in your intro note."
  },
  {
    id: "levels-fyi",
    name: "Levels.fyi Internship Radar",
    category: "Internships & Comp",
    url: "https://www.levels.fyi/internships/",
    description: "Real-time verified internship openings, stipends, and international company hiring timelines.",
    badge: "Verified Comp",
    icon: "📈",
    tips: "Check stipend benchmarks and look for companies actively opening application cycles."
  },
  {
    id: "simplify-jobs",
    name: "Simplify.jobs",
    category: "Internship Tracker",
    url: "https://simplify.jobs/",
    description: "Automated internship aggregator tracking 500+ tech internships and new grad roles with 1-click autofill.",
    badge: "1-Click Tracking",
    icon: "⚡",
    tips: "Keep your profile updated to match live openings instantly as companies post them."
  },
  {
    id: "github-tracker",
    name: "GitHub SWE / AI Internship Tracker",
    category: "Community Open Source",
    url: "https://github.com/SimplifyJobs/Summer2025-Internships",
    description: "The most active open-source list of tech internships, updated hourly with role status and locations.",
    badge: "Open Source",
    icon: "🐙",
    tips: "Watch/star the repo to get instant notifications when HFT and FAANG applications go live."
  },
  {
    id: "otta",
    name: "Otta (Welcome to the Jungle)",
    category: "Curated Tech Roles",
    url: "https://otta.com/",
    description: "Smart matching platform for fast-growing scaleups and top international tech companies in Europe & US.",
    badge: "Curated",
    icon: "✨",
    tips: "High quality job descriptions with explicit remote flexibility and company values."
  },
  {
    id: "remoteok",
    name: "RemoteOK",
    category: "100% Remote",
    url: "https://remoteok.com/",
    description: "Dedicated global board for worldwide remote software engineering, AI, and backend positions.",
    badge: "Remote Worldwide",
    icon: "🌍",
    tips: "Filter by 'Worldwide' to view positions with zero geographic hiring restrictions."
  },
  {
    id: "honeypot",
    name: "Honeypot.io",
    category: "Europe Tech",
    url: "https://www.honeypot.io/en/",
    description: "Developer-focused reverse hiring platform where German, Dutch, and European tech companies apply to you.",
    badge: "Europe Focused",
    icon: "🇪🇺",
    tips: "Companies here routinely provide visa support and relocation packages for qualified developers."
  },
  {
    id: "relocate-me",
    name: "Relocate.me",
    category: "Visa Sponsorship",
    url: "https://relocate.me/",
    description: "Verified tech jobs with explicit visa sponsorship and relocation assistance across Europe and Asia.",
    badge: "Visa Sponsored",
    icon: "✈️",
    tips: "Ideal for searching verified European sponsors without guessing eligibility."
  }
];

export const COMPANIES_DATA = [
  // 1. FAANG / BIG TECH
  {
    name: "Google",
    category: "FAANG / Big Tech",
    region: "Global / US / India",
    focus: "DSA + AI/ML + Distributed Systems",
    url: "https://careers.google.com/jobs/results/",
    priority: "Dream",
    priorityLevel: "🔴",
    tags: ["SWE", "AI/ML", "Cloud", "DSA"],
    hiringWindow: "Aug - Nov (Summer Internships) & Year-round"
  },
  {
    name: "Microsoft",
    category: "FAANG / Big Tech",
    region: "Global / India / US",
    focus: "Strong student & early-career university hiring",
    url: "https://jobs.careers.microsoft.com/global/en/search",
    priority: "High Value",
    priorityLevel: "🟠",
    tags: ["SWE", "AI", "Cloud"],
    hiringWindow: "Aug - Oct (Campus & Off-Campus)"
  },
  {
    name: "NVIDIA",
    category: "FAANG / Big Tech",
    region: "Global / US / India / Europe",
    focus: "GPU Computing, CUDA, AI/ML systems & LLMs",
    url: "https://nvidia.wd5.myworkdayjobs.com/en-US/NVIDIAExternalCareerSite",
    priority: "High Value",
    priorityLevel: "🟠",
    tags: ["C++", "CUDA", "AI/ML", "Systems"],
    hiringWindow: "Sep - Dec & Year-round"
  },
  {
    name: "Meta",
    category: "FAANG / Big Tech",
    region: "Global / US / UK",
    focus: "High-scale systems, PyTorch, AI infrastructure",
    url: "https://www.metacareers.com/jobs",
    priority: "Dream",
    priorityLevel: "🔴",
    tags: ["SWE", "AI/ML", "PyTorch", "Scale"],
    hiringWindow: "Aug - Nov"
  },
  {
    name: "Amazon",
    category: "FAANG / Big Tech",
    region: "Global / India / Europe",
    focus: "Massive scale SWE & Cloud infrastructure",
    url: "https://www.amazon.jobs/en/search",
    priority: "High Value",
    priorityLevel: "🟠",
    tags: ["SWE", "AWS", "Backend"],
    hiringWindow: "Aug - Dec (Rolling)"
  },
  {
    name: "Apple",
    category: "FAANG / Big Tech",
    region: "US / Europe / Global",
    focus: "Core OS, on-device ML, performance C++",
    url: "https://jobs.apple.com/en-us/search",
    priority: "Dream",
    priorityLevel: "🔴",
    tags: ["C++", "ML", "Systems", "OS"],
    hiringWindow: "Sep - Jan"
  },
  {
    name: "Adobe",
    category: "FAANG / Big Tech",
    region: "Global / India / US",
    focus: "Firefly GenAI, Computer Vision & Product SWE",
    url: "https://adobe.wd5.myworkdayjobs.com/external_experienced",
    priority: "Opportunity",
    priorityLevel: "🟢",
    tags: ["GenAI", "C++", "Computer Vision"],
    hiringWindow: "Sep - Dec"
  },
  {
    name: "Salesforce",
    category: "FAANG / Big Tech",
    region: "Global / India / US",
    focus: "Agentforce, Enterprise AI, Distributed SaaS",
    url: "https://salesforce.wd12.myworkdayjobs.com/SalesforceCareers",
    priority: "Opportunity",
    priorityLevel: "🟢",
    tags: ["AI Agents", "Cloud", "SaaS"],
    hiringWindow: "Aug - Nov"
  },

  // 2. HFT / QUANT / TRADING
  {
    name: "Jane Street",
    category: "HFT / Quant",
    region: "US / UK / Europe / Hong Kong / Singapore",
    focus: "Advanced Algorithms, C++, OCaml, Quantitative Engineering",
    url: "https://www.janestreet.com/join-jane-street/open-roles/",
    priority: "High Value",
    priorityLevel: "🟠",
    tags: ["C++", "Algorithms", "Quant", "Top Comp"],
    hiringWindow: "July - Oct (Opens very early!)"
  },
  {
    name: "Hudson River Trading (HRT)",
    category: "HFT / Quant",
    region: "US / UK / Europe / Singapore / India",
    focus: "Ultra-low latency C++, Systems architecture, Algorithms",
    url: "https://www.hudsonrivertrading.com/careers/",
    priority: "High Value",
    priorityLevel: "🟠",
    tags: ["C++", "Low-Latency", "Systems", "DSA"],
    hiringWindow: "July - Nov"
  },
  {
    name: "Optiver",
    category: "HFT / Quant",
    region: "Netherlands (Amsterdam) / US / Singapore / UK",
    focus: "10-week SWE, FPGA, and Quant internships with Europe visa sponsorship",
    url: "https://www.optiver.com/working-at-optiver/career-opportunities/",
    priority: "High Value",
    priorityLevel: "🟠",
    tags: ["C++", "Quant", "Europe Hub", "Top Stipend"],
    hiringWindow: "Aug - Dec"
  },
  {
    name: "IMC Trading",
    category: "HFT / Quant",
    region: "Amsterdam / US / India (Mumbai) / Sydney",
    focus: "C++/Java coding assessments, APAC & European student pipelines",
    url: "https://www.imc.com/careers/",
    priority: "Opportunity",
    priorityLevel: "🟢",
    tags: ["C++", "Java", "India Office", "Trading"],
    hiringWindow: "Aug - Jan"
  },
  {
    name: "Citadel / Citadel Securities",
    category: "HFT / Quant",
    region: "US / Europe / Singapore / Hong Kong",
    focus: "Pioneering SWE, quantitative research, market making",
    url: "https://www.citadelsecurities.com/careers/open-roles/",
    priority: "Dream",
    priorityLevel: "🔴",
    tags: ["C++", "Distributed Systems", "Quant"],
    hiringWindow: "July - Oct"
  },
  {
    name: "Jump Trading",
    category: "HFT / Quant",
    region: "US / UK / Europe / Singapore",
    focus: "High performance systems, low-latency algorithms, C++",
    url: "https://www.jumptrading.com/careers/",
    priority: "High Value",
    priorityLevel: "🟠",
    tags: ["C++", "Systems", "HFT"],
    hiringWindow: "Aug - Nov"
  },
  {
    name: "DRW",
    category: "HFT / Quant",
    region: "US / Europe / Singapore",
    focus: "Quantitative trading, software engineering, algorithms",
    url: "https://www.drw.com/careers",
    priority: "Opportunity",
    priorityLevel: "🟢",
    tags: ["SWE", "C++", "Trading"],
    hiringWindow: "Sep - Dec"
  },
  {
    name: "Flow Traders",
    category: "HFT / Quant",
    region: "Netherlands (Amsterdam) / US / Singapore",
    focus: "Leading liquidity provider, global trading infrastructure",
    url: "https://www.flowtraders.com/careers/vacancies",
    priority: "Opportunity",
    priorityLevel: "🟢",
    tags: ["C++", "Europe", "Fintech"],
    hiringWindow: "Aug - Dec"
  },
  {
    name: "Tower Research Capital",
    category: "HFT / Quant",
    region: "India (Gurugram) / US / Europe / Singapore",
    focus: "Quantitative trading & low latency systems in India and globally",
    url: "https://www.tower-research.com/open-positions",
    priority: "High Value",
    priorityLevel: "🟠",
    tags: ["C++", "DSA", "India Office", "Quant"],
    hiringWindow: "Aug - Jan"
  },

  // 3. FRONTIER AI & GENAI
  {
    name: "Mistral AI",
    category: "Frontier AI & GenAI",
    region: "France (Paris) / Europe / Global",
    focus: "Open frontier LLMs (Mixtral, Le Chat, Codestral), efficient AI models",
    url: "https://jobs.lever.co/mistral",
    priority: "High Value",
    priorityLevel: "🟠",
    tags: ["LLMs", "GenAI", "Python", "Europe"],
    hiringWindow: "Year-round (High Growth)"
  },
  {
    name: "DeepL",
    category: "Frontier AI & GenAI",
    region: "Germany (Cologne) / Europe / Remote",
    focus: "World-class Language AI, neural machine translation, LLMs",
    url: "https://jobs.lever.co/deepl",
    priority: "High Value",
    priorityLevel: "🟠",
    tags: ["NLP", "PyTorch", "Europe Tech", "AI/ML"],
    hiringWindow: "Year-round"
  },
  {
    name: "Hugging Face",
    category: "Frontier AI & GenAI",
    region: "US / France / 100% Remote",
    focus: "The home of open-source AI, Transformers, Diffusers, Hub",
    url: "https://apply.workable.com/huggingface/",
    priority: "High Value",
    priorityLevel: "🟠",
    tags: ["Open Source", "Remote", "Python", "LLMs"],
    hiringWindow: "Year-round"
  },
  {
    name: "Cohere",
    category: "Frontier AI & GenAI",
    region: "Canada / UK / US / Remote",
    focus: "Enterprise foundation models, Command R+, RAG embeddings",
    url: "https://jobs.lever.co/cohere",
    priority: "Opportunity",
    priorityLevel: "🟢",
    tags: ["RAG", "Embeddings", "LLMs"],
    hiringWindow: "Sep - Dec & Year-round"
  },
  {
    name: "Scale AI",
    category: "Frontier AI & GenAI",
    region: "US / Global / Remote",
    focus: "AI infrastructure, generative AI evaluation, data pipelines",
    url: "https://boards.greenhouse.io/scaleai",
    priority: "High Value",
    priorityLevel: "🟠",
    tags: ["AI Infra", "MLOps", "Fullstack"],
    hiringWindow: "Aug - Jan"
  },
  {
    name: "Cursor (Anysphere)",
    category: "Frontier AI & GenAI",
    region: "US / Remote",
    focus: "AI-first code editor, frontier coding models, agentic workflows",
    url: "https://jobs.ashbyhq.com/anysphere",
    priority: "High Value",
    priorityLevel: "🟠",
    tags: ["AI Agents", "TypeScript", "C++", "Startups"],
    hiringWindow: "Year-round"
  },
  {
    name: "Perplexity AI",
    category: "Frontier AI & GenAI",
    region: "US / Remote",
    focus: "Conversational search engine, real-time RAG, LLM indexing",
    url: "https://boards.greenhouse.io/perplexityai",
    priority: "High Value",
    priorityLevel: "🟠",
    tags: ["RAG", "Search", "Python", "Fast Growth"],
    hiringWindow: "Year-round"
  },
  {
    name: "Together AI",
    category: "Frontier AI & GenAI",
    region: "US / Remote",
    focus: "Fastest cloud platform for open-source AI inference & fine-tuning",
    url: "https://jobs.lever.co/together",
    priority: "Opportunity",
    priorityLevel: "🟢",
    tags: ["Inference", "CUDA", "Distributed ML"],
    hiringWindow: "Year-round"
  },
  {
    name: "Helsing",
    category: "Frontier AI & GenAI",
    region: "Germany (Munich) / UK / France",
    focus: "Live AI sensing, deep tech, embedded edge computing",
    url: "https://helsing.ai/careers",
    priority: "Opportunity",
    priorityLevel: "🟢",
    tags: ["Deep Tech", "C++", "Europe Unicorn"],
    hiringWindow: "Year-round"
  },

  // 4. EUROPEAN TECH UNICORNS
  {
    name: "ASML",
    category: "European Product & Tech",
    region: "Netherlands (Veldhoven)",
    focus: "Semiconductor lithography, advanced C++ & machine intelligence",
    url: "https://www.asml.com/en/careers",
    priority: "High Value",
    priorityLevel: "🟠",
    tags: ["C++", "Semiconductors", "Deep Tech"],
    hiringWindow: "Aug - Jan"
  },
  {
    name: "Adyen",
    category: "European Product & Tech",
    region: "Netherlands (Amsterdam) / Europe / Global",
    focus: "Global financial technology platform, high-throughput distributed systems",
    url: "https://careers.adyen.com/",
    priority: "High Value",
    priorityLevel: "🟠",
    tags: ["Distributed Systems", "Java", "Europe Hub"],
    hiringWindow: "Sep - Dec"
  },
  {
    name: "Booking.com",
    category: "European Product & Tech",
    region: "Netherlands (Amsterdam) / Europe",
    focus: "Large-scale recommendation systems, ML models, high traffic SWE",
    url: "https://careers.booking.com/",
    priority: "High Value",
    priorityLevel: "🟠",
    tags: ["ML", "SWE", "Visa Sponsorship"],
    hiringWindow: "Aug - Dec"
  },
  {
    name: "Celonis",
    category: "European Product & Tech",
    region: "Germany (Munich) / US / Global",
    focus: "Process Intelligence Graph, Enterprise AI, C++ core engine",
    url: "https://www.celonis.com/careers/",
    priority: "Opportunity",
    priorityLevel: "🟢",
    tags: ["C++", "Enterprise AI", "Germany"],
    hiringWindow: "Sep - Jan"
  },
  {
    name: "Scandit",
    category: "European Product & Tech",
    region: "Switzerland (Zurich) / Europe",
    focus: "Mobile Computer Vision, C++, Smart Data Capture",
    url: "https://www.scandit.com/company/careers/",
    priority: "Opportunity",
    priorityLevel: "🟢",
    tags: ["Computer Vision", "C++", "Switzerland"],
    hiringWindow: "Year-round"
  },

  // 5. CLOUD, INFRA & DEVTOOLS
  {
    name: "Databricks",
    category: "Cloud, Infra & DevTools",
    region: "US / Europe / India / Global",
    focus: "Apache Spark, MLflow, Delta Lake, enterprise GenAI platform",
    url: "https://www.databricks.com/company/careers",
    priority: "High Value",
    priorityLevel: "🟠",
    tags: ["Data + AI", "C++", "Python", "Top Tier"],
    hiringWindow: "Aug - Nov"
  },
  {
    name: "Cloudflare",
    category: "Cloud, Infra & DevTools",
    region: "Global / Europe / US / Remote",
    focus: "Workers AI, edge compute, networking, Rust/C++ systems",
    url: "https://www.cloudflare.com/careers/",
    priority: "High Value",
    priorityLevel: "🟠",
    tags: ["Edge AI", "Rust", "Networks"],
    hiringWindow: "Sep - Dec"
  },
  {
    name: "Vercel",
    category: "Cloud, Infra & DevTools",
    region: "US / Europe / 100% Remote",
    focus: "Next.js, AI SDK, frontend cloud infrastructure",
    url: "https://vercel.com/careers",
    priority: "High Value",
    priorityLevel: "🟠",
    tags: ["React", "AI SDK", "Cloud", "Remote"],
    hiringWindow: "Year-round"
  },
  {
    name: "MongoDB",
    category: "Cloud, Infra & DevTools",
    region: "Global / India / US",
    focus: "Vector Search, distributed database engine, modern cloud",
    url: "https://www.mongodb.com/careers",
    priority: "Opportunity",
    priorityLevel: "🟢",
    tags: ["C++", "Vector DB", "Distributed Systems"],
    hiringWindow: "Aug - Nov"
  },
  {
    name: "GitLab",
    category: "Cloud, Infra & DevTools",
    region: "100% Remote Worldwide",
    focus: "All-remote pioneer, AI Duo, DevOps platform",
    url: "https://about.gitlab.com/jobs/",
    priority: "High Value",
    priorityLevel: "🟠",
    tags: ["100% Remote", "DevOps", "Ruby", "Go"],
    hiringWindow: "Year-round"
  },

  // 6. 100% REMOTE / GLOBAL
  {
    name: "Automattic",
    category: "100% Remote / Distributed",
    region: "100% Remote Worldwide (83+ Countries)",
    focus: "WordPress.com, Tumblr, PocketCasts, async-first engineering",
    url: "https://automattic.com/work-with-us/",
    priority: "High Value",
    priorityLevel: "🟠",
    tags: ["Remote Worldwide", "Async", "PHP", "React"],
    hiringWindow: "Year-round"
  },
  {
    name: "Canonical (Ubuntu)",
    category: "100% Remote / Distributed",
    region: "100% Remote Worldwide",
    focus: "Ubuntu Linux, cloud native Kubernetes, AI at the edge",
    url: "https://canonical.com/careers",
    priority: "Opportunity",
    priorityLevel: "🟢",
    tags: ["Linux", "C++", "Python", "Remote"],
    hiringWindow: "Year-round (Active tests)"
  },
  {
    name: "Zapier",
    category: "100% Remote / Distributed",
    region: "100% Remote Worldwide",
    focus: "Workflow automation, Central AI Agents, serverless microservices",
    url: "https://zapier.com/jobs",
    priority: "Opportunity",
    priorityLevel: "🟢",
    tags: ["AI Agents", "Python", "Remote"],
    hiringWindow: "Year-round"
  },

  // 7. HIGH-GROWTH STARTUPS & AGENT TECH
  {
    name: "Browser Use",
    category: "High-Growth Startups & YC",
    region: "Remote / US",
    focus: "Open-source AI browser automation, agents connecting LLMs to web",
    url: "https://www.browser-use.com/",
    priority: "High Value",
    priorityLevel: "🟠",
    tags: ["AI Agents", "Playwright", "Python", "Direct Fit"],
    hiringWindow: "Year-round"
  },
  {
    name: "ElevenLabs",
    category: "High-Growth Startups & YC",
    region: "US / UK / Europe / Remote",
    focus: "Conversational Voice AI, generative audio research, realtime WebSockets",
    url: "https://elevenlabs.io/careers",
    priority: "High Value",
    priorityLevel: "🟠",
    tags: ["Audio AI", "Python", "Fast Growth"],
    hiringWindow: "Year-round"
  },
  {
    name: "Modal",
    category: "High-Growth Startups & YC",
    region: "US / Remote",
    focus: "Serverless cloud compute for AI/ML teams, Rust & Python infrastructure",
    url: "https://modal.com/careers",
    priority: "Opportunity",
    priorityLevel: "🟢",
    tags: ["ML Infra", "Rust", "Python"],
    hiringWindow: "Year-round"
  },
  {
    name: "Linear",
    category: "High-Growth Startups & YC",
    region: "Remote / US / Europe",
    focus: "High performance issue tracker, local-first sync engines, craft",
    url: "https://linear.app/careers",
    priority: "Opportunity",
    priorityLevel: "🟢",
    tags: ["TypeScript", "Product SWE", "Remote"],
    hiringWindow: "Year-round"
  },

  // 8. APAC / JAPAN / SINGAPORE
  {
    name: "Sakana AI",
    category: "APAC / Japan / Singapore",
    region: "Japan (Tokyo)",
    focus: "Nature-inspired evolutionary AI models, model merging, AI Scientist",
    url: "https://sakana.ai/careers/",
    priority: "High Value",
    priorityLevel: "🟠",
    tags: ["AI Research", "Tokyo", "PyTorch"],
    hiringWindow: "Year-round"
  },
  {
    name: "Mercari",
    category: "APAC / Japan / Singapore",
    region: "Japan (Tokyo) / Europe",
    focus: "Global marketplace app, English-speaking engineering culture in Tokyo",
    url: "https://careers.mercari.com/en/",
    priority: "High Value",
    priorityLevel: "🟠",
    tags: ["Japan Visa", "Go", "ML", "Relocation"],
    hiringWindow: "Aug - Dec & Year-round"
  },
  {
    name: "Grab",
    category: "APAC / Japan / Singapore",
    region: "Singapore / India (Bengaluru) / APAC",
    focus: "Southeast Asia superapp, real-time routing, fintech, AI matching",
    url: "https://www.grab.careers/",
    priority: "Opportunity",
    priorityLevel: "🟢",
    tags: ["India Office", "Go", "Microservices"],
    hiringWindow: "Sep - Dec"
  }
];

export const HIRING_CALENDAR = [
  {
    phase: "Phase 1: Early Openers (July - September)",
    title: "HFTs & Frontier US/Europe Internship Openings",
    description: "HFT companies (Jane Street, HRT, Optiver, Citadel) open their summer pipelines first. FAANG opens university portals.",
    targets: ["Jane Street", "HRT", "Optiver", "Google", "Microsoft", "Databricks"],
    action: "Have your C++/DSA fundamentals and resume PDF polished. Apply within the first 48 hours of posting."
  },
  {
    phase: "Phase 2: Peak Season (September - November)",
    title: "Big Tech, European Scaleups & Enterprise AI",
    description: "Peak application window across US and European tech ecosystems. Campus off-campus drives accelerate.",
    targets: ["NVIDIA", "Adyen", "Booking.com", "Celonis", "Mistral AI", "DeepL", "Cloudflare"],
    action: "Run targeted LinkedIn alumni outreach. Request referrals with concrete project demonstrations."
  },
  {
    phase: "Phase 3: Spring & Off-Cycle (January - April)",
    title: "AI Startups, YC Batches & 100% Remote Teams",
    description: "High-growth startups, newly funded YC companies, and remote-first teams hire based on immediate project needs.",
    targets: ["Browser Use", "Cursor", "Perplexity", "Modal", "Automattic", "GitLab", "Zapier"],
    action: "Showcase deployed agentic & RAG web demos directly to founders and team leads on GitHub/X/LinkedIn."
  },
  {
    phase: "Phase 4: Rolling / Year-Round",
    title: "Open-Source & Deep Tech Hiring",
    description: "Continuous hiring pipeline driven by contribution, skill challenges, and specialized domain expertise.",
    targets: ["Hugging Face", "Canonical", "Together AI", "ElevenLabs", "Sakana AI"],
    action: "Contribute to relevant open-source libraries or build extensions showcasing their API ecosystem."
  }
];

export const OUTREACH_TEMPLATES = [
  {
    title: "Connection Request (LinkedIn - Max 300 Chars)",
    text: "Hi [Name], I'm a BTech AI/ML student building GenAI & autonomous agent workflows with C++/Python/React. I came across your engineering work at [Company] and would love to connect and follow your journey!"
  },
  {
    title: "Specific Role Referral Request",
    text: "Hi [Name], I saw the [Role Title] opening (Req ID: [ID]) at [Company] and was thrilled to see its focus on [DSA / LLMs / Systems]. I've built and deployed [Your Project Name], an autonomous agent platform built with FastAPI and Playwright. If my background looks aligned, would you be open to submitting an internal referral? Here is my resume: [Resume Link]. Thank you so much for your time!"
  },
  {
    title: "Startup Founder / Hiring Lead Cold Message",
    text: "Hi [Name], huge fan of what [Company] is building with [Product/Tech]. I built an interactive demonstration combining [Tech Stack: e.g. RAG + Browser Automation] that addresses [Specific Problem/Feature]. You can test the live demo here: [Demo URL] and inspect the GitHub codebase: [GitHub URL]. Would love to contribute to the team as an SWE/AI Intern!"
  }
];
