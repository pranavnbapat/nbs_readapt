# NbS ReAdapt — End-User Guide

**Version:** 1.0  
**Date:** 2026-05-11  
**Audience:** Researchers, policymakers, practitioners, project managers  
**Status:** Current as of v1 release

---

## Table of Contents

1. [Getting Started](#1-getting-started)
2. [Home Page & Guided Discovery](#2-home-page--guided-discovery)
3. [Search & Browse](#3-search--browse)
4. [Evidence Map](#4-evidence-map)
5. [Policy Explorer](#5-policy-explorer)
6. [Analytics Dashboard](#6-analytics-dashboard)
7. [Research Gaps](#7-research-gaps)
8. [NbS Assistant (AI Chat)](#8-nbs-assistant-ai-chat)
9. [Shortlist & Briefing Generation](#9-shortlist--briefing-generation)
10. [About the Project](#10-about-the-project)
11. [Tips & Troubleshooting](#11-tips--troubleshooting)

---

## 1. Getting Started

### 1.1 What is NbS ReAdapt?

The **NbS ReAdapt Knowledge Repository** is a curated database of evidence on **Nature-based Solutions (NbS)** for climate adaptation in Europe. It brings together:

- **Academic papers and reports** (~410)
- **Network projects and case studies** (~103)
- **EU-funded projects** (~275)
- **Policies** — EU and national (~769)

Whether you are a researcher looking for peer-reviewed studies, a policymaker comparing regulations, or a practitioner seeking practical case studies, this platform helps you find relevant evidence quickly.

### 1.2 Accessing the Platform

Open your web browser and navigate to the platform URL:

```
https://nbs-readapt.example.com/
```

*(Replace with your organization's actual domain)*

The platform works best on modern browsers (Chrome, Firefox, Safari, Edge) with JavaScript enabled.

### 1.3 Interface Overview

The platform is organized as a **single-page application** with a top navigation bar containing these tabs:

| Tab | Purpose |
|-----|---------|
| **Home** | Guided entry point — pick hazard, territory, and scale |
| **Search & Browse** | Full faceted search with filters and result cards |
| **Evidence Map** | Interactive map of geolocated evidence |
| **Policy Explorer** | Dedicated browser for all 769+ policies |
| **Analytics** | Dashboard with metrics, charts, and insights |
| **Research Gaps** | Evidence gap analysis and priority areas |
| **NbS Assistant** | AI-powered Q&A grounded in repository data |
| **About** | Project description, partners, and methodology |

---

## 2. Home Page & Guided Discovery

### 2.1 Using the Landing Page

The **Home** tab is designed to help you narrow down to relevant evidence in three steps:

#### Step 1: Select a Climate Hazard

Click on one or more hazards from the picker:
- Flooding
- Wildfires
- Drought
- Urban Heat
- Coastal Erosion
- Landslides
- Storms
- ... and more

#### Step 2: Select Territory Type

Choose the geographic scope you are interested in:
- **Country** — Single nation studies
- **Multi-country** — Cross-national comparisons
- **Supranational** — EU-wide or continental
- **Transnational region** — River basins, mountain ranges, etc.
- **Local/Place** — City or site-specific

#### Step 3: Select Governance Scale

Pick the implementation or policy level:
- Local / Municipal
- Regional
- National
- EU / International

### 2.2 Live Map Preview

As you make selections, the **mini-map** on the home page updates to show matching records. This gives you an immediate visual sense of where evidence exists.

### 2.3 Explore Button

Once you have made your selections, click the **Explore** button. This takes you directly to the **Search & Browse** tab with your filters pre-applied.

---

## 3. Search & Browse

### 3.1 Free-Text Search

At the top of the **Search & Browse** tab, you will find a search box. Type keywords to search across:

- Record titles
- Abstracts and summaries
- Descriptions
- Keywords

**Tips:**
- Use specific terms (e.g., "green roof" rather than just "green")
- The search uses relevance ranking — the most relevant results appear first
- Leave the search box empty and click search to see all records

### 3.2 Using Filters

The left sidebar contains multiple filter categories. You can combine filters across categories:

| Filter | What It Does | Example Values |
|--------|--------------|----------------|
| **Dataset** | Limit to source type | Papers, Network Projects, EU Funded Projects, Policies |
| **Country** | Filter by geography | Germany, Spain, Italy, ... |
| **Geography Type** | Filter by scope | Country, Multi-country, Supranational, ... |
| **Hazard** | Climate hazard focus | Flooding, Urban Heat, Drought, ... |
| **NbS Type** | Type of nature-based solution | Green infrastructure, Blue infrastructure, Forest restoration, ... |
| **Implementation Stage** | Project maturity | Planning, Implementation, Monitoring, Completed |
| **Policy Level** | Policy hierarchy | EU, National, Regional, Local |
| **Year Range** | Publication or start year | 2000–2026 slider |

**How filters work:**
- Selecting multiple values **within** the same filter uses **OR** logic (e.g., Flooding OR Drought)
- Selecting values **across** different filters uses **AND** logic (e.g., Flooding AND Germany)
- The result count updates immediately as you apply filters

### 3.3 Understanding Result Cards

Each search result appears as a card containing:

- **Title** — Click to expand full details
- **Dataset badge** — Color-coded by source type
- **Year** — Publication or project start year
- **Country / Geography** — Where the evidence applies
- **Hazard tags** — Primary climate hazards
- **NbS tags** — Primary nature-based solution types
- **Abstract / Summary** — Brief description

### 3.4 Practitioner View

If you are a practitioner looking for actionable insights, toggle the **Practitioner View** switch. This changes the card layout to prominently display:

- Lessons learned
- Barriers encountered
- Enablers (success factors)
- Implementation steps

### 3.5 Record Detail Modal

Click any result card to open a **detail modal** showing:

- Complete metadata (all available fields)
- Full abstract, summary, or description
- Outcomes and impacts
- Governance and finance insights
- Source URLs (clickable links to original documents)
- Related taxonomy tags

Click the **+** button on a card or in the modal to add the record to your **Shortlist**.

---

## 4. Evidence Map

### 4.1 Overview

The **Evidence Map** tab shows all geolocated records on an interactive world map. This is useful for:

- Seeing geographic clustering of evidence
- Finding cases near your region
- Identifying underserved areas

### 4.2 Map Controls

| Control | Function |
|---------|----------|
| **Zoom** | Mouse wheel or +/- buttons |
| **Pan** | Click and drag |
| **Pin click** | Open record detail |
| **Filter panel** | Show/hide pins by NbS type, hazard, or domain |

### 4.3 Color Modes

Use the **Color by** dropdown to change pin colors:

- **NbS Type** — Each type has a distinct color (e.g., green for green infrastructure, blue for blue infrastructure)
- **Hazard** — Each hazard has a distinct color (e.g., red for wildfires, cyan for flooding)

### 4.4 Choropleth Overlay

Toggle **Country Coverage** to see a choropleth layer:

- Countries with more evidence appear darker
- Countries with no evidence remain uncolored
- Click a colored country to jump to search filtered by that country

### 4.5 Map Tips

- Use the filter panel to reduce pin clutter in dense regions
- Zoom into Europe for the densest concentration of evidence
- The map works on mobile devices with touch gestures

---

## 5. Policy Explorer

### 5.1 What is the Policy Explorer?

The **Policy Explorer** is a dedicated interface for browsing all **769+ policy records** in the repository. It is optimized for policymakers and legal researchers who need to:

- Compare policies across countries
- Assess legal bindingness
- Track NbS mentions in legislation

### 5.2 Policy Filters

The left sidebar offers policy-specific filters:

| Filter | Description |
|--------|-------------|
| **Country** | EU member states and neighbors |
| **Legal Bindingness** | Binding, Non-binding, or Mixed |
| **NbS Type** | Which nature-based solutions are addressed |
| **Hazard** | Which climate hazards are covered |
| **Text Search** | Free-text within policy titles and descriptions |

### 5.3 Policy Cards

Policy result cards show:
- Document title
- Policy level (EU, National, Regional, Local)
- Legal bindingness badge
- Year
- Country
- NbS and hazard tags

### 5.4 CSV Export

After filtering, click the **Export CSV** button to download the filtered policy list as a spreadsheet. This is useful for:
- Offline analysis
- Inclusion in reports
- Further sorting and filtering in Excel

---

## 6. Analytics Dashboard

### 6.1 Overview Metrics

The **Analytics** tab opens with high-level numbers:

- **Total Records** — Complete repository count
- **By Dataset** — Breakdown: Papers, Cases, EU Projects, Policies
- **By Implementation Stage** — Planning, Implementation, Monitoring, Completed
- **By Year** — Timeline histogram showing evidence publication over time

### 6.2 Choropleth Mini-Maps

Two interactive choropleth maps show:

1. **Hazard by Country** — Which hazards are most studied in each country
2. **NbS Type by Country** — Which solutions are most common in each country

Each map has a **ranking sidebar** showing the top countries for the selected dimension.

### 6.3 Evidence Density Matrix

A large grid shows the intersection of **NbS Types** (rows) and **Hazards** (columns):

- Each cell shows how many records address that combination
- Darker/greener cells = more evidence
- Lighter cells = less evidence
- Toggle between **Count** and **Percentage** views
- Click any cell to search for that specific combination

### 6.4 Country Deep-Dive

Click any country on a choropleth map to open a **Country Deep-Dive** modal:

- Total records for that country
- Breakdown by dataset
- Top hazards and NbS types
- Direct link to browse all records

---

## 7. Research Gaps

### 7.1 What are Research Gaps?

A **research gap** is an NbS–hazard combination with very little evidence (fewer than 3 records). Identifying gaps helps:

- Funding agencies prioritize calls
- Researchers choose underexplored topics
- Policymakers understand where evidence is thin

### 7.2 Gap Matrix

The **Research Gaps** tab shows the same NbS × Hazard matrix as Analytics, but with a focus on empty or sparse cells:

- **Red cells** = gaps (< 3 records)
- **Orange cells** = weak coverage (3–5 records)
- **Green cells** = adequate coverage (> 5 records)

### 7.3 Priority Gap List

Below the matrix, a **Priority List** shows the most significant gaps ranked by:

- Absolute deficit (how many records are missing)
- Relative deficit (percentage of expected coverage)

Use this list to identify the highest-impact research opportunities.

---

## 8. NbS Assistant (AI Chat)

### 8.1 What is the NbS Assistant?

The **NbS Assistant** is an AI-powered chatbot that answers questions about the repository content. It uses a technique called **Retrieval-Augmented Generation (RAG)**:

1. You ask a question
2. The system searches the repository for relevant records
3. It sends those records to an AI model as context
4. The AI generates an answer grounded in real evidence

### 8.2 Getting Started

1. Click the **NbS Assistant** tab
2. If prompted, enter your API key (this is stored only in your browser)
3. Type your question in the chat box
4. Press Enter or click Send

### 8.3 Example Questions

The assistant can handle questions like:

> "What are the main barriers to implementing urban green infrastructure?"

> "Compare EU-funded wetland restoration projects in Northern and Southern Europe."

> "Which policies in Germany address flooding through nature-based solutions?"

> "What lessons have been learned from coastal NbS projects in Spain?"

> "What funding sources are most common for urban heat adaptation projects?"

### 8.4 Response Styles

You can choose how detailed you want the answer:

| Style | Best For |
|-------|----------|
| **Brief** | Quick facts, yes/no, single-answer questions |
| **Standard** | Balanced explanation with some detail |
| **Detailed** | In-depth analysis with examples and nuance |

### 8.5 Understanding Citations

Every AI response includes **source citations** at the bottom. Each citation shows:
- Record title
- Dataset (Papers, Projects, Policies)
- Year
- Country
- Relevance score
- Link to view the full record

**Important:** Always verify critical information against the original source. The AI summarizes content but may occasionally misinterpret details.

### 8.6 Conversation History

The assistant remembers your conversation within the session. You can:
- Ask follow-up questions
- Reference previous answers
- Clear the conversation to start fresh

---

## 9. Shortlist & Briefing Generation

### 9.1 Building Your Shortlist

As you browse records, click the **+** button on any card to add it to your **Shortlist**. The shortlist:

- Appears as a slide-out drawer from the right side
- Shows all saved records with remove buttons
- Displays a count badge on the shortlist icon
- Persists across tab switches (stored in your browser)

### 9.2 Managing Your Shortlist

In the shortlist drawer, you can:
- **Remove** individual records (× button)
- **Clear all** records (trash button)
- **Reorder** records (drag and drop, if supported)

### 9.3 Generating a Briefing

Once you have selected relevant records, click **Generate Briefing**. This opens a new page with:

- A **summary section** — Overview of selected records
- **Tag analysis** — Common hazards, NbS types, countries, and years
- **Detailed record blocks** — Full content of each shortlisted record
- **Print-friendly styling** — Optimized for printing or saving as PDF

To save as PDF:
1. Click **Generate Briefing**
2. In the new tab, press `Ctrl+P` (Windows) or `Cmd+P` (Mac)
3. Select "Save as PDF" as the destination
4. Choose your preferred layout (Portrait or Landscape)

### 9.4 Use Cases for Briefings

- **Project proposals** — Attach relevant evidence
- **Policy briefs** — Support recommendations with case studies
- **Stakeholder reports** — Share findings with partners
- **Academic reviews** — Compile literature for systematic reviews

---

## 10. About the Project

### 10.1 ESPON ReAdapt

The NbS ReAdapt Knowledge Repository is part of the **ESPON ReAdapt** project, which investigates Nature-based Solutions for climate adaptation across European territories.

### 10.2 Partners

The project involves research institutions, policy organizations, and spatial planning experts from across Europe.

### 10.3 Methodology

Evidence is collected through:
1. Systematic literature review (academic databases)
2. Project database mining (EU funding programmes)
3. Policy document analysis (EU and national legal frameworks)
4. Network case study collection (practitioner submissions)

All records undergo normalization to ensure consistent taxonomy and geography classification.

---

## 11. Tips & Troubleshooting

### 11.1 General Tips

| Tip | Explanation |
|-----|-------------|
| **Start broad, then narrow** | Use the Home page for initial filtering, then refine in Search |
| **Combine filters** | The most powerful searches use multiple filter categories |
| **Check the map** | Geographic patterns reveal clusters and gaps |
| **Use Practitioner View** | If you need actionable insights, not just academic abstracts |
| **Save to shortlist** | Build a collection as you explore; generate a briefing at the end |
| **Verify AI answers** | Always check source citations for critical decisions |

### 11.2 Common Issues

| Issue | Solution |
|-------|----------|
| **Search returns no results** | Clear some filters or try broader keywords |
| **Map shows no pins** | Check that your filters are not too restrictive |
| **AI assistant not responding** | Check your API key; the service may be temporarily unavailable |
| **Shortlist disappeared** | Shortlist is stored in your browser — clearing cookies removes it |
| **Page loads slowly** | The bootstrap API caches for 5 minutes; first load may take a few seconds |

### 11.3 Browser Recommendations

- **Chrome** or **Firefox** — Best performance and compatibility
- **Safari** — Fully supported
- **Edge** — Fully supported
- **Mobile browsers** — Supported; interface adapts to smaller screens

### 11.4 Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Esc` | Close modals |
| `Ctrl+F` / `Cmd+F` | Find on page (works within current tab) |
| `Ctrl+P` / `Cmd+P` | Print briefing page |

---

## Feedback & Support

If you encounter issues or have suggestions for improving the platform, please contact your system administrator or project coordinator.

For technical issues, include:
- Your browser and version
- The page/tab you were using
- The filters or search terms applied
- Any error messages shown

---

**Document Owner:** User Experience Lead  
**Review Cycle:** Quarterly  
**Last Updated:** 2026-05-11
