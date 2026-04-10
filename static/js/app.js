(function () {
  const EUROPE_BOUNDS = [
    [27.5, -25.0],
    [71.5, 45.0],
  ];

  const state = {
    map: null,
    markers: [],
    landingMap: null,
    landingMarkers: [],
    analytics: null,
    facets: null,
    shortlist: [],
    lastQueryPayload: null,
    topFacets: null,
  };

  const els = {
    tabs: document.querySelectorAll(".tablink"),
    panels: document.querySelectorAll(".tabpanel"),
    tabTargets: document.querySelectorAll("[data-tab-target]"),
    searchInput: document.getElementById("search-input"),
    runSearch: document.getElementById("run-search"),
    resetFilters: document.getElementById("reset-filters"),
    resultsMeta: document.getElementById("results-meta"),
    activeFilters: document.getElementById("active-filters"),
    resultsList: document.getElementById("results-list"),
    landingMap: document.getElementById("landing-map"),
    landingMapCount: document.getElementById("landing-map-count"),
    landingMapLegend: document.getElementById("landing-map-legend"),
    homeHazardGrid: document.getElementById("home-hazard-grid"),
    homeGeographyPills: document.getElementById("home-geography-pills"),
    homeDatasetPills: document.getElementById("home-dataset-pills"),
    mapMeta: document.getElementById("map-meta"),
    mapList: document.getElementById("map-list"),
    filters: {
      source_dataset: document.getElementById("filter-source-dataset"),
      country: document.getElementById("filter-country"),
      geography_type: document.getElementById("filter-geography-type"),
      hazard: document.getElementById("filter-hazard"),
      nbs_type: document.getElementById("filter-nbs-type"),
      implementation_stage: document.getElementById("filter-implementation-stage"),
      policy_level: document.getElementById("filter-policy-level"),
      year_gte: document.getElementById("filter-year-gte"),
      year_lte: document.getElementById("filter-year-lte"),
    },
    analyticsDatasets: document.getElementById("analytics-datasets"),
    analyticsImplementation: document.getElementById("analytics-implementation"),
    analyticsYears: document.getElementById("analytics-years"),
    analyticsHazards: document.getElementById("analytics-hazards"),
    analyticsNbs: document.getElementById("analytics-nbs"),
    shortlistMeta: document.getElementById("shortlist-meta"),
    shortlistItems: document.getElementById("shortlist-items"),
    clearShortlist: document.getElementById("clear-shortlist"),
    modal: document.getElementById("record-modal"),
    closeModal: document.getElementById("close-modal"),
    modalType: document.getElementById("modal-type"),
    modalTitle: document.getElementById("modal-title"),
    modalMeta: document.getElementById("modal-meta"),
    modalSummary: document.getElementById("modal-summary"),
    modalSections: document.getElementById("modal-sections"),
  };

  const hazardIcons = {
    Flooding: "🌊",
    "Extreme temperature events": "🌡️",
    "Precipitation extremes and drought": "🏜️",
    "Sea level rise and coastal change": "🌊",
    "Storms and cyclones": "🌪️",
    Wildfires: "🔥",
    "Biological hazards": "🦠",
    "Oceanic change": "🌊",
    "Land degradation": "🌱",
    "Cryosphere change": "❄️",
    "Air pollution": "🌫️",
  };

  const hazardColors = {
    Flooding: "#2f80c8",
    "Extreme temperature events": "#d97706",
    "Precipitation extremes and drought": "#d9a441",
    "Sea level rise and coastal change": "#2aa6a4",
    "Storms and cyclones": "#7c5ce0",
    Wildfires: "#d94841",
    "Biological hazards": "#48a868",
    "Oceanic change": "#2389b5",
    "Land degradation": "#879b2b",
    "Cryosphere change": "#5b7be3",
    "Air pollution": "#7e8794",
  };

  function loadShortlist() {
    try {
      state.shortlist = JSON.parse(localStorage.getItem("nbs_shortlist") || "[]");
    } catch (_error) {
      state.shortlist = [];
    }
  }

  function saveShortlist() {
    localStorage.setItem("nbs_shortlist", JSON.stringify(state.shortlist));
  }

  function selectedValues(select) {
    return Array.from(select.selectedOptions).map((option) => option.value).filter(Boolean);
  }

  function buildParams(options = {}) {
    const params = new URLSearchParams();
    const q = els.searchInput.value.trim();
    if (q) params.set("q", q);

    Object.entries(els.filters).forEach(([key, element]) => {
      if (!element) return;
      if (element.tagName === "SELECT") {
        selectedValues(element).forEach((value) => params.append(key, value));
      } else if (element.value.trim()) {
        params.set(key, element.value.trim());
      }
    });

    Object.entries(options).forEach(([key, value]) => {
      params.set(key, value);
    });
    return params;
  }

  function populateSelect(select, items) {
    const previous = new Set(selectedValues(select));
    select.innerHTML = "";
    items.forEach((item) => {
      const option = document.createElement("option");
      option.value = item.key;
      option.textContent = `${item.key} (${item.doc_count})`;
      if (previous.has(item.key)) option.selected = true;
      select.appendChild(option);
    });
  }

  function facetSelected(key, value) {
    const select = els.filters[key];
    if (!select) return false;
    return Array.from(select.selectedOptions).some((option) => option.value === value);
  }

  function toggleFacetSelection(key, value) {
    const select = els.filters[key];
    if (!select) return;
    const option = Array.from(select.options).find((item) => item.value === value);
    if (!option) return;
    option.selected = !option.selected;
    runSearch().catch(handleError);
  }

  function attachQuickFilterHandlers(container, key) {
    if (!container) return;
    container.querySelectorAll("[data-filter-value]").forEach((button) => {
      button.addEventListener("click", () => toggleFacetSelection(key, button.dataset.filterValue));
    });
  }

  function renderQuickFacetButtons() {
    if (els.homeHazardGrid) {
      const hazards = (state.facets?.hazards || []).slice(0, 6);
      els.homeHazardGrid.innerHTML = hazards
        .map((item) => {
          const active = facetSelected("hazard", item.key) ? "active" : "";
          const icon = hazardIcons[item.key] || "📍";
          return `
            <button class="hazard-card ${active}" type="button" data-filter-value="${item.key}">
              <div class="hazard-card-top">
                <span class="hazard-icon">${icon}</span>
                <span>
                  <span class="hazard-name">${item.key}</span>
                  <span class="hazard-count">${item.doc_count} records</span>
                </span>
              </div>
            </button>
          `;
        })
        .join("");
      attachQuickFilterHandlers(els.homeHazardGrid, "hazard");
    }

    if (els.homeGeographyPills) {
      const geography = (state.facets?.geography_type || []).slice(0, 6);
      els.homeGeographyPills.innerHTML = geography
        .map((item) => {
          const active = facetSelected("geography_type", item.key) ? "active" : "";
          return `<button class="ter-pill ${active}" type="button" data-filter-value="${item.key}">${item.key}</button>`;
        })
        .join("");
      attachQuickFilterHandlers(els.homeGeographyPills, "geography_type");
    }

    if (els.homeDatasetPills) {
      const datasets = state.facets?.source_dataset || [];
      els.homeDatasetPills.innerHTML = datasets
        .map((item) => {
          const active = facetSelected("source_dataset", item.key) ? "active" : "";
          const label = item.key.replaceAll("_", " ");
          return `<button class="ter-pill ${active}" type="button" data-filter-value="${item.key}">${label}</button>`;
        })
        .join("");
      attachQuickFilterHandlers(els.homeDatasetPills, "source_dataset");
    }
  }

  function renderFilterChips() {
    const chips = [];
    const labels = {
      source_dataset: "Dataset",
      country: "Country",
      geography_type: "Geography",
      hazard: "Hazard",
      nbs_type: "NbS",
      implementation_stage: "Stage",
      policy_level: "Policy",
      year_gte: "From",
      year_lte: "To",
    };

    Object.entries(els.filters).forEach(([key, element]) => {
      if (element.tagName === "SELECT") {
        selectedValues(element).forEach((value) => chips.push(`${labels[key]}: ${value}`));
      } else if (element.value.trim()) {
        chips.push(`${labels[key]}: ${element.value.trim()}`);
      }
    });
    if (els.searchInput.value.trim()) chips.unshift(`Search: ${els.searchInput.value.trim()}`);

    els.activeFilters.innerHTML = chips.map((chip) => `<span class="filter-chip">${chip}</span>`).join("");
  }

  function summaryText(record) {
    return (
      record.summary ||
      record.description ||
      record.abstract ||
      record.objective ||
      record.lessons ||
      "No summary available for this record yet."
    );
  }

  function resultMeta(record) {
    const parts = [
      record.source_dataset,
      record.publication_year || record.start_year || record.end_year,
      record.country_display,
      record.geography_type,
      record.implementation_stage,
    ].filter(Boolean);
    return parts.map((part) => `<span class="pill">${part}</span>`).join("");
  }

  function resultTags(record) {
    const tags = []
      .concat((record.all_hazards || []).slice(0, 3))
      .concat((record.all_nbs_types || []).slice(0, 3))
      .slice(0, 6);
    return tags.map((tag) => `<span class="pill">${tag}</span>`).join("");
  }

  function shortlistHas(recordId) {
    return state.shortlist.some((item) => item.id === recordId);
  }

  function toggleShortlist(record) {
    if (shortlistHas(record.id)) {
      state.shortlist = state.shortlist.filter((item) => item.id !== record.id);
    } else {
      state.shortlist = [
        {
          id: record.id,
          title: record.title,
          source_dataset: record.source_dataset,
          country_display: record.country_display,
        },
        ...state.shortlist,
      ].slice(0, 20);
    }
    saveShortlist();
    renderShortlist();
    if (state.lastQueryPayload) renderResults(state.lastQueryPayload);
  }

  function renderShortlist() {
    if (!state.shortlist.length) {
      els.shortlistMeta.textContent = "No records shortlisted yet.";
      els.shortlistItems.innerHTML = `<div class="empty-state">Use “Shortlist” on search results to build a working set for comparison and handoff.</div>`;
      return;
    }
    els.shortlistMeta.textContent = `${state.shortlist.length} saved record${state.shortlist.length > 1 ? "s" : ""}.`;
    els.shortlistItems.innerHTML = state.shortlist
      .map(
        (item) => `
          <div class="shortlist-card">
            <strong>${item.title}</strong>
            <div class="result-meta">
              <span class="pill">${item.source_dataset.replaceAll("_", " ")}</span>
              ${item.country_display ? `<span class="pill">${item.country_display}</span>` : ""}
            </div>
          </div>
        `
      )
      .join("");
  }

  function buildDetailSections(record) {
    const sections = [
      ["Abstract", record.abstract],
      ["Summary", record.summary],
      ["Description", record.description],
      ["Objective", record.objective],
      ["Outcomes Targeted", record.outcomes_targeted],
      ["Ecological Impacts", record.ecological_impacts],
      ["Socio-economic Impacts", record.socio_economic_impacts],
      ["Governance Insights", record.governance_insights],
      ["Finance Insights", record.finance_insights],
      ["Implementation Steps", record.implementation_steps],
      ["Barriers", record.barriers],
      ["Enablers", record.enablers],
      ["Lessons", record.lessons],
      ["Monitoring / Reporting", record.monitoring_reporting],
      ["Keywords", record.keywords],
    ].filter(([, value]) => value && String(value).trim());

    return sections
      .map(
        ([title, value]) => `
          <section class="detail-section">
            <h3>${title}</h3>
            <p>${String(value)}</p>
          </section>
        `
      )
      .join("");
  }

  async function openRecordModal(record) {
    const detail = await fetchJson(`/repository/records/${record.record_id || record.id}/`);
    const hydrated = {
      ...record,
      ...detail,
      all_hazards: [...new Set([...(detail.primary_hazards || []), ...(detail.secondary_hazards || [])])],
      all_nbs_types: [...new Set([...(detail.primary_nbs_types || []), ...(detail.secondary_nbs_types || [])])],
    };
    els.modalType.textContent = hydrated.source_dataset.replaceAll("_", " ");
    els.modalTitle.textContent = hydrated.title;
    els.modalMeta.innerHTML = `${resultMeta(hydrated)}${resultTags(hydrated)}<span class="pill">UID ${hydrated.source_uid}</span>`;
    els.modalSummary.textContent = summaryText(hydrated);
    els.modalSections.innerHTML = buildDetailSections(hydrated);
    els.modal.classList.add("open");
  }

  function closeRecordModal() {
    els.modal.classList.remove("open");
  }

  function renderResults(payload) {
    state.lastQueryPayload = payload;
    els.resultsMeta.textContent = `${payload.total} matching records`;
    if (!payload.hits.length) {
      els.resultsList.innerHTML = `<div class="empty-state">No records matched the current search and filter combination.</div>`;
      return;
    }

    els.resultsList.innerHTML = payload.hits
      .map((record) => {
        const url = record.source_url || record.source_url_secondary || "";
        const shortlisted = shortlistHas(record.id);
        return `
          <article class="result-card">
            <div class="result-top">
              <div>
                <div class="result-type">${record.source_dataset.replaceAll("_", " ")}</div>
                <h3 class="result-title">${record.title}</h3>
                <p class="result-summary">${summaryText(record)}</p>
                <div class="result-meta">${resultMeta(record)}</div>
                <div class="result-tags">${resultTags(record)}</div>
                <div class="card-actions">
                  <button class="mini-btn" data-action="detail" data-id="${record.id}">Open Detail</button>
                  <button class="mini-btn ${shortlisted ? "active" : ""}" data-action="shortlist" data-id="${record.id}">
                    ${shortlisted ? "Shortlisted" : "Shortlist"}
                  </button>
                </div>
              </div>
              <div class="result-score">
                <div>Score</div>
                <strong>${(record.score || 0).toFixed(1)}</strong>
                ${url ? `<div style="margin-top:10px"><a href="${url}" target="_blank" rel="noreferrer">Source</a></div>` : ""}
              </div>
            </div>
          </article>
        `;
      })
      .join("");

    els.resultsList.querySelectorAll("[data-action='detail']").forEach((button) => {
      button.addEventListener("click", () => {
        const record = payload.hits.find((item) => item.id === button.dataset.id);
        if (record) openRecordModal(record).catch(handleError);
      });
    });
    els.resultsList.querySelectorAll("[data-action='shortlist']").forEach((button) => {
      button.addEventListener("click", () => {
        const record = payload.hits.find((item) => item.id === button.dataset.id);
        if (record) toggleShortlist(record);
      });
    });
  }

  async function fetchJson(url) {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Request failed: ${response.status}`);
    }
    return response.json();
  }

  async function refreshFacets() {
    const payload = await fetchJson(`/search/facets/?${buildParams().toString()}`);
    state.facets = payload;
    populateSelect(els.filters.source_dataset, payload.source_dataset || []);
    populateSelect(els.filters.country, payload.countries || []);
    populateSelect(els.filters.geography_type, payload.geography_type || []);
    populateSelect(els.filters.hazard, payload.hazards || []);
    populateSelect(els.filters.nbs_type, payload.nbs_types || []);
    populateSelect(els.filters.implementation_stage, payload.implementation_stage || []);
    populateSelect(els.filters.policy_level, payload.policy_level || []);
    renderQuickFacetButtons();
  }

  function clearMarkerSet(markers) {
    markers.forEach((marker) => marker.remove());
    markers.length = 0;
  }

  function markerColor(record) {
    const hazard = (record.all_hazards || [])[0];
    return hazardColors[hazard] || "#2f9b73";
  }

  function ensureMap() {
    if (state.map) return state.map;
    state.map = L.map("map-canvas", { scrollWheelZoom: true });
    L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", {
      subdomains: "abcd",
      maxZoom: 20,
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
    }).addTo(state.map);
    state.map.fitBounds(EUROPE_BOUNDS, { padding: [12, 12] });
    return state.map;
  }

  function ensureLandingMap() {
    if (!els.landingMap) return null;
    if (state.landingMap) return state.landingMap;
    state.landingMap = L.map("landing-map", { zoomControl: true, scrollWheelZoom: true });
    L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", {
      subdomains: "abcd",
      maxZoom: 20,
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
    }).addTo(state.landingMap);
    state.landingMap.fitBounds(EUROPE_BOUNDS, { padding: [12, 12] });
    return state.landingMap;
  }

  function renderLandingLegend(points) {
    if (!els.landingMapLegend) return;
    const used = [];
    points.forEach((record) => {
      const hazard = (record.all_hazards || [])[0] || "Other";
      if (!used.includes(hazard)) used.push(hazard);
    });
    els.landingMapLegend.innerHTML = used.slice(0, 6)
      .map((hazard) => {
        const color = hazardColors[hazard] || "#2f9b73";
        return `<span class="legend-item"><span class="legend-dot" style="background:${color}"></span>${hazard}</span>`;
      })
      .join("");
  }

  function renderLandingMap(payload) {
    const map = ensureLandingMap();
    if (!map) return;
    clearMarkerSet(state.landingMarkers);
    const points = payload.hits.filter((record) => Number.isFinite(record.latitude) && Number.isFinite(record.longitude));

    if (!points.length) {
      map.fitBounds(EUROPE_BOUNDS, { padding: [12, 12] });
      if (els.landingMapCount) els.landingMapCount.textContent = "";
      if (els.landingMapLegend) els.landingMapLegend.innerHTML = "";
      return;
    }

    const bounds = [];
    points.forEach((record) => {
      const color = markerColor(record);
      const marker = L.circleMarker([record.latitude, record.longitude], {
        radius: 4.5,
        color: "#ffffff",
        weight: 1.4,
        fillColor: color,
        fillOpacity: 0.95,
      }).addTo(map);
      marker.bindPopup(`<strong>${record.title}</strong><br>${record.country_display || ""}`);
      state.landingMarkers.push(marker);
      bounds.push([record.latitude, record.longitude]);
    });
    map.fitBounds(bounds, { padding: [30, 30], maxZoom: 4 });
    if (els.landingMapCount) {
      els.landingMapCount.textContent = `${points.length} mapped results`;
    }
    renderLandingLegend(points);
  }

  function renderMap(payload) {
    const map = ensureMap();
    clearMarkerSet(state.markers);
    const points = payload.hits.filter((record) => Number.isFinite(record.latitude) && Number.isFinite(record.longitude));

    if (!points.length) {
      els.mapMeta.textContent = "No geocoded results for the current search state.";
      els.mapList.innerHTML = "";
      map.fitBounds(EUROPE_BOUNDS, { padding: [12, 12] });
      return;
    }

    const bounds = [];
    points.forEach((record) => {
      const color = markerColor(record);
      const marker = L.circleMarker([record.latitude, record.longitude], {
        radius: 7,
        color: "#ffffff",
        weight: 1.2,
        fillColor: color,
        fillOpacity: 0.92,
      }).addTo(map);
      marker.bindPopup(`<strong>${record.title}</strong><br>${record.country_display || ""}`);
      state.markers.push(marker);
      bounds.push([record.latitude, record.longitude]);
    });
    map.fitBounds(bounds, { padding: [30, 30], maxZoom: 5 });
    els.mapMeta.textContent = `${points.length} mapped records from the current search state.`;
    els.mapList.innerHTML = points
      .slice(0, 6)
      .map(
        (record) => `
          <div class="compact-item">
            <strong>${record.title}</strong>
            <div class="subtle">${record.geography_label || record.country_display || "Unknown location"}</div>
          </div>
        `
      )
      .join("");
  }

  function renderStackList(target, items, keyField) {
    if (!items.length) {
      target.innerHTML = `<div class="empty-state">No data available.</div>`;
      return;
    }
    const max = Math.max(...items.map((item) => item.doc_count), 1);
    target.innerHTML = items
      .map((item) => {
        const width = `${(item.doc_count / max) * 100}%`;
        return `
          <div class="stack-row">
            <div class="label">
              <strong>${item[keyField]}</strong>
              <div class="bar" style="width:${width}"></div>
            </div>
            <div class="value">${item.doc_count}</div>
          </div>
        `;
      })
      .join("");
  }

  function renderYearBars(items) {
    if (!items.length) {
      els.analyticsYears.innerHTML = `<div class="empty-state">No year data available.</div>`;
      return;
    }
    const max = Math.max(...items.map((item) => item.doc_count), 1);
    els.analyticsYears.innerHTML = items
      .map((item) => {
        const height = Math.max(16, Math.round((item.doc_count / max) * 180));
        return `<div class="year-bar" style="height:${height}px" title="${item.source_year}: ${item.doc_count}"><span>${item.source_year}</span></div>`;
      })
      .join("");
  }

  async function refreshAnalytics() {
    const [payload, topFacets] = await Promise.all([
      fetchJson("/repository/overview/"),
      fetchJson("/search/facets/"),
    ]);
    state.analytics = payload;
    state.topFacets = topFacets;
    renderStackList(els.analyticsDatasets, payload.dataset_counts || [], "source_dataset");
    renderStackList(els.analyticsImplementation, payload.implementation_stage || [], "implementation_stage");
    renderYearBars(payload.year_counts || []);
    renderStackList(els.analyticsHazards, (topFacets.hazards || []).slice(0, 8), "key");
    renderStackList(els.analyticsNbs, (topFacets.nbs_types || []).slice(0, 8), "key");
  }

  async function runSearch() {
    renderFilterChips();
    const [queryPayload, mapPayload] = await Promise.all([
      fetchJson(`/search/query/?${buildParams({ size: 40 }).toString()}`),
      fetchJson(`/search/query/?${buildParams({ size: 250 }).toString()}`),
    ]);
    renderResults(queryPayload);
    renderLandingMap(mapPayload);
    renderMap(mapPayload);
    await refreshFacets();
  }

  function resetFilters() {
    els.searchInput.value = "";
    Object.values(els.filters).forEach((element) => {
      if (element.tagName === "SELECT") {
        Array.from(element.options).forEach((option) => {
          option.selected = false;
        });
      } else {
        element.value = "";
      }
    });
    runSearch().catch(handleError);
  }

  function handleError(error) {
    console.error(error);
    els.resultsMeta.textContent = "Something went wrong while loading data.";
    els.resultsList.innerHTML = `<div class="empty-state">${error.message}</div>`;
  }

  function switchTab(nextTab) {
    els.tabs.forEach((button) => button.classList.toggle("active", button.dataset.tab === nextTab));
    els.panels.forEach((panel) => panel.classList.toggle("active", panel.dataset.panel === nextTab));
    setTimeout(() => {
      if (nextTab === "map" && state.map) state.map.invalidateSize();
      if (nextTab === "home" && state.landingMap) state.landingMap.invalidateSize();
    }, 50);
  }

  els.tabs.forEach((button) => {
    button.addEventListener("click", () => switchTab(button.dataset.tab));
  });
  els.tabTargets.forEach((button) => {
    button.addEventListener("click", () => switchTab(button.dataset.tabTarget));
  });
  els.runSearch.addEventListener("click", () => runSearch().catch(handleError));
  els.resetFilters.addEventListener("click", resetFilters);
  els.clearShortlist.addEventListener("click", () => {
    state.shortlist = [];
    saveShortlist();
    renderShortlist();
    if (state.lastQueryPayload) renderResults(state.lastQueryPayload);
  });
  els.closeModal.addEventListener("click", closeRecordModal);
  els.modal.addEventListener("click", (event) => {
    if (event.target === els.modal) closeRecordModal();
  });
  els.searchInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      runSearch().catch(handleError);
    }
  });
  Object.values(els.filters).forEach((element) => {
    element.addEventListener("change", () => runSearch().catch(handleError));
  });

  loadShortlist();
  renderShortlist();
  Promise.all([refreshAnalytics(), runSearch()]).catch(handleError);
})();
