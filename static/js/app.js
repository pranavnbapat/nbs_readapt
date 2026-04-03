(function () {
  const state = {
    map: null,
    markers: [],
    analytics: null,
    facets: null,
    shortlist: [],
    lastQueryPayload: null,
    topFacets: null,
  };

  const els = {
    tabs: document.querySelectorAll(".tablink"),
    panels: document.querySelectorAll(".tabpanel"),
    searchInput: document.getElementById("search-input"),
    runSearch: document.getElementById("run-search"),
    resetFilters: document.getElementById("reset-filters"),
    resultsMeta: document.getElementById("results-meta"),
    activeFilters: document.getElementById("active-filters"),
    resultsList: document.getElementById("results-list"),
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
  }

  function clearMarkers() {
    state.markers.forEach((marker) => marker.remove());
    state.markers = [];
  }

  function ensureMap() {
    if (state.map) return state.map;
    state.map = L.map("map-canvas", { scrollWheelZoom: true }).setView([51.2, 10.5], 4);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; OpenStreetMap contributors",
    }).addTo(state.map);
    return state.map;
  }

  function renderMap(payload) {
    const map = ensureMap();
    clearMarkers();
    const points = payload.hits.filter((record) => Number.isFinite(record.latitude) && Number.isFinite(record.longitude));

    if (!points.length) {
      els.mapMeta.textContent = "No geocoded results for the current search state.";
      els.mapList.innerHTML = "";
      map.setView([51.2, 10.5], 4);
      return;
    }

    const bounds = [];
    points.forEach((record) => {
      const marker = L.circleMarker([record.latitude, record.longitude], {
        radius: 7,
        color: "#237849",
        weight: 1,
        fillColor: "#89b68a",
        fillOpacity: 0.85,
      }).addTo(map);
      marker.bindPopup(`<strong>${record.title}</strong><br>${record.country_display || ""}`);
      state.markers.push(marker);
      bounds.push([record.latitude, record.longitude]);
    });
    map.fitBounds(bounds, { padding: [30, 30] });
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
    if (nextTab === "map" && state.map) {
      setTimeout(() => state.map.invalidateSize(), 50);
    }
  }

  els.tabs.forEach((button) => {
    button.addEventListener("click", () => switchTab(button.dataset.tab));
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
