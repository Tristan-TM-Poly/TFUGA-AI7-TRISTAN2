const DATA_URL = './data/infra_qc_demo_bundle.json';

const $ = (selector) => document.querySelector(selector);

function badge(value) {
  const safe = String(value ?? 'unknown').toLowerCase().replace(/[^a-z0-9_-]/g, '-');
  return `<span class="badge ${safe}">${value ?? 'unknown'}</span>`;
}

function text(value) {
  return value === undefined || value === null || value === '' ? '—' : String(value);
}

function renderAssets(assets) {
  $('#assets').innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Asset</th>
          <th>Sector</th>
          <th>Owner</th>
          <th>Visibility</th>
          <th>Criticality</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        ${assets
          .map(
            (asset) => `
          <tr>
            <td>${text(asset.name)}</td>
            <td>${text(asset.sector)}</td>
            <td>${text(asset.owner_type)}</td>
            <td>${badge(asset.visibility)}</td>
            <td>${text(asset.criticality)}</td>
            <td>${text(asset.condition_status)}</td>
          </tr>
        `,
          )
          .join('')}
      </tbody>
    </table>
  `;
}

function renderRisks(risks) {
  $('#risks').innerHTML = risks
    .map(
      (risk) => `
    <article class="metric-card">
      <h3>${text(risk.asset_id)}</h3>
      ${badge(risk.band)}
      <p class="meta">Pressure: ${text(risk.pressure)} · Maintenance priority: ${text(risk.maintenance_priority)}</p>
      <p class="meta">Public dependency: ${text(risk.public_dependency)} · Climate: ${text(risk.climate_exposure)} · Sensitivity: ${text(risk.privacy_security_sensitivity)}</p>
    </article>
  `,
    )
    .join('');
}

function renderMaintenance(signals) {
  $('#maintenance').innerHTML = signals
    .map(
      (signal) => `
    <article class="metric-card">
      <h3>${text(signal.asset_id)}</h3>
      ${badge(signal.band)}
      <p class="meta">Priority: ${text(signal.priority_score)}</p>
      <p class="meta">Needs more evidence: ${text(signal.needs_more_evidence)}</p>
    </article>
  `,
    )
    .join('');
}

function renderScenarios(scenarios) {
  $('#scenarios').innerHTML = scenarios
    .map(
      (scenario) => `
    <article class="metric-card">
      <h3>${text(scenario.name)}</h3>
      ${badge(scenario.band)}
      <p class="meta">Kind: ${text(scenario.kind)}</p>
      <p class="meta">Affected asset count: ${text(scenario.affected_asset_count)}</p>
    </article>
  `,
    )
    .join('');
}

function renderSources(sources) {
  $('#sources').innerHTML = sources
    .map(
      (source) => `
    <article class="metric-card">
      <h3>${text(source.title)}</h3>
      ${badge(source.permission)}
      <p class="meta">Kind: ${text(source.kind)}</p>
      <p class="meta">Source ID: ${text(source.source_id)}</p>
    </article>
  `,
    )
    .join('');
}

function renderEvidence(items) {
  $('#evidence').innerHTML = items
    .map(
      (item) => `
    <article class="metric-card">
      <h3>${text(item.evidence_id)}</h3>
      ${badge(item.status)}
      <p class="meta">${text(item.claim)}</p>
      <p class="meta">Confidence: ${text(item.confidence)} · Method: ${text(item.method)}</p>
    </article>
  `,
    )
    .join('');
}

function render(bundle) {
  const graph = bundle.graph ?? {};
  const quality = graph.quality ?? {};
  const gate = bundle.security_gate ?? {};

  $('#security-status').textContent = text(gate.status);
  $('#security-status').className = gate.status ? `badge ${gate.status}` : '';
  $('#security-note').textContent = gate.publishable
    ? 'Public-safe demo bundle is publishable.'
    : 'Review required before publication.';
  $('#asset-count').textContent = text(quality.asset_count);
  $('#dependency-count').textContent = text(quality.dependency_count);
  $('#public-safe').textContent = text(bundle.public_safe);

  renderAssets(graph.assets ?? []);
  renderRisks(bundle.risks ?? []);
  renderMaintenance(bundle.maintenance ?? []);
  renderScenarios(bundle.scenarios ?? []);
  renderSources(bundle.sources?.sources ?? []);
  renderEvidence(bundle.evidence?.items ?? []);
}

async function load() {
  try {
    const response = await fetch(DATA_URL);
    if (!response.ok) {
      throw new Error(`Unable to load ${DATA_URL}: ${response.status}`);
    }
    const bundle = await response.json();
    render(bundle);
  } catch (error) {
    $('#security-status').textContent = 'error';
    $('#security-note').textContent = error.message;
    console.error(error);
  }
}

load();
