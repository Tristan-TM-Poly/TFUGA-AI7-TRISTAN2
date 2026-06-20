const state = {
  mode: "sage-architect",
  oak: "OAK-4",
  constraints: new Set(["zero-touch", "oak-boundary", "negative-memory", "github-artifacts"]),
  branches: new Set(["TFUGA", "HGFM", "OAK", "SAGE", "Bayes-Tristan"]),
  actions: new Set(["create-files", "tests", "workflow"]),
  quality: new Set(["distinguish-claim-status", "residue-log", "prototype-first"]),
};

const data = {
  modes: [
    ["sage-architect", "SAGE Architect", "Architecture, canon, modules, interfaces"],
    ["oak-verifier", "OAK Verifier", "Preuves, tests, falsification, résidus"],
    ["github-builder", "GitHub Builder", "Fichiers, tests, workflows, runbooks"],
    ["publication-atlas", "Publication Atlas", "Université, professeur, dossier publication"],
    ["data-harvester", "Open Data Harvester", "Sources, licenses, manifests, benchmarks"],
    ["spectro-lab", "Spectro Lab", "FFWT/HAC/CVCD, signaux, datasets"],
    ["math-proof", "Math Proof", "Définitions, théorèmes, preuves, contre-exemples"]
  ],
  constraints: [
    ["zero-touch", "ZÉRO-TOUCH", "Minimiser actions manuelles"],
    ["oak-boundary", "Frontière OAK", "Vision ≠ preuve ≠ mesure"],
    ["negative-memory", "Mémoire M−", "Capturer erreurs et anti-patterns"],
    ["github-artifacts", "Artifacts GitHub", "Créer fichiers, tests, workflows"],
    ["no-overclaim", "Anti-survente", "Claims bornés et vérifiables"],
    ["french", "Français", "Répondre en français par défaut"]
  ],
  branches: ["TFUGA", "TGTM", "HGFM", "CVCD", "OAK", "SAGE", "AIT", "Bayes-Tristan", "FFWT-HAC-CVCD", "Publication Atlas", "Open Data Harvester", "AIT-Universe", "Math Universe", "Spectro Universe", "Materials", "AI7"],
  actions: [
    ["create-files", "Créer fichiers repo"],
    ["tests", "Ajouter tests"],
    ["workflow", "Ajouter workflow CI"],
    ["docs", "Documenter"],
    ["runbook", "Créer runbook"],
    ["schemas", "Ajouter schémas JSON"],
    ["benchmarks", "Créer benchmark"],
    ["publication-package", "Générer package publication"]
  ],
  quality: [
    ["distinguish-claim-status", "Distinguer vision / formalisation / prototype / mesure / preuve"],
    ["residue-log", "Ajouter log de résidus"],
    ["prototype-first", "Prioriser prototype testable"],
    ["security-boundary", "Respecter sécurité, permissions, vie privée"],
    ["citations-if-public", "Citations si informations publiques actuelles"],
    ["small-safe-steps", "Limiter explosions récursives / fichiers énormes"]
  ]
};

const $ = (id) => document.getElementById(id);

function toast(message) {
  const box = $("toast");
  box.textContent = message;
  box.classList.add("show");
  setTimeout(() => box.classList.remove("show"), 2300);
}

function renderModes() {
  const root = $("modeList");
  root.innerHTML = "";
  data.modes.forEach(([id, title, subtitle]) => {
    const btn = document.createElement("button");
    btn.className = `mode-card ${state.mode === id ? "active" : ""}`;
    btn.innerHTML = `<strong>${title}</strong><span>${subtitle}</span>`;
    btn.addEventListener("click", () => { state.mode = id; renderAll(); });
    root.appendChild(btn);
  });
}

function renderChips() {
  const root = $("constraintChips");
  root.innerHTML = "";
  data.constraints.forEach(([id, title, subtitle]) => {
    const chip = document.createElement("button");
    chip.className = `chip ${state.constraints.has(id) ? "active" : ""}`;
    chip.innerHTML = `<span><strong>${title}</strong><br><small>${subtitle}</small></span><span>${state.constraints.has(id) ? "✓" : "+"}</span>`;
    chip.addEventListener("click", () => toggleSet(state.constraints, id));
    root.appendChild(chip);
  });
}

function renderChecks(rootId, items, setRef) {
  const root = $(rootId);
  root.innerHTML = "";
  items.forEach((item) => {
    const id = Array.isArray(item) ? item[0] : item;
    const label = Array.isArray(item) ? item[1] : item;
    const row = document.createElement("label");
    row.className = "check-row";
    row.innerHTML = `<input type="checkbox" ${setRef.has(id) ? "checked" : ""} /><span>${label}</span>`;
    row.querySelector("input").addEventListener("change", () => toggleSet(setRef, id));
    root.appendChild(row);
  });
}

function toggleSet(setRef, id) {
  if (setRef.has(id)) setRef.delete(id); else setRef.add(id);
  renderAll();
}

function oakButtons() {
  document.querySelectorAll("[data-oak]").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.oak === state.oak);
    btn.onclick = () => { state.oak = btn.dataset.oak; renderAll(); };
  });
}

function selectedLabels(items, setRef) {
  return items
    .filter((item) => setRef.has(Array.isArray(item) ? item[0] : item))
    .map((item) => Array.isArray(item) ? item[1] : item);
}

function getModeTitle() {
  return data.modes.find(([id]) => id === state.mode)?.[1] || state.mode;
}

function buildPrompt() {
  const title = $("sessionTitle").value.trim() || "Ω-SAGE Session";
  const mission = $("mission").value.trim();
  const outputMode = $("outputMode").value;
  const extra = $("constraints").value.trim();
  const branchList = [...state.branches].join(", ");
  const actionList = selectedLabels(data.actions, state.actions).join("; ");
  const qualityList = selectedLabels(data.quality, state.quality).join("; ");
  const constraintList = selectedLabels(data.constraints, state.constraints).join("; ");

  return `# ${title}\n\nTu es ChatGPT dans l’interface personnalisée ChatGPT × Tristan OS.\n\n## Mode SAGE actif\n${getModeTitle()}\n\n## Mission\n${mission}\n\n## Sortie attendue\n${outputMode}\n\n## Branches Tristan à intégrer\n${branchList}\n\n## Actions souhaitées\n${actionList}\n\n## Niveau OAK cible\n${state.oak}\n\n## Contraintes permanentes\n${constraintList}\n\n## Qualité obligatoire\n${qualityList}\n\n## Contraintes additionnelles\n${extra}\n\n## Règles de réponse\n- Répondre en français.\n- Construire un résultat directement utile.\n- Préférer fichiers, patchs, tests, workflows, manifests ou checklists quand pertinent.\n- Distinguer clairement : vision fertile, formalisation, prototype, mesure, preuve.\n- Ajouter M− : erreurs possibles, limites, résidus, anti-survente.\n- Ne pas promettre de travail futur; produire maintenant ce qui est possible.\n- Si GitHub ou outils sont disponibles, privilégier ZÉRO-TOUCH.\n\nGO MAX PLUS ULTRA, mais OAK-safe.`;
}

function updatePrompt() {
  $("promptOutput").value = buildPrompt();
}

function sessionPayload() {
  return {
    version: "chatgpt-tristan-interface.v1",
    saved_at: new Date().toISOString(),
    title: $("sessionTitle").value,
    mission: $("mission").value,
    outputMode: $("outputMode").value,
    constraintsText: $("constraints").value,
    state: {
      mode: state.mode,
      oak: state.oak,
      constraints: [...state.constraints],
      branches: [...state.branches],
      actions: [...state.actions],
      quality: [...state.quality]
    }
  };
}

function applySession(payload) {
  $("sessionTitle").value = payload.title || "Ω-SAGE Session";
  $("mission").value = payload.mission || "";
  $("outputMode").value = payload.outputMode || "architecture + actions concrètes";
  $("constraints").value = payload.constraintsText || "";
  if (payload.state) {
    state.mode = payload.state.mode || state.mode;
    state.oak = payload.state.oak || state.oak;
    state.constraints = new Set(payload.state.constraints || []);
    state.branches = new Set(payload.state.branches || []);
    state.actions = new Set(payload.state.actions || []);
    state.quality = new Set(payload.state.quality || []);
  }
  renderAll();
}

function saveSession() {
  const payload = sessionPayload();
  const key = `chatgpt-tristan:${Date.now()}`;
  localStorage.setItem(key, JSON.stringify(payload));
  toast("Session sauvée localement");
  renderSessions();
}

function renderSessions() {
  const root = $("sessionList");
  root.innerHTML = "";
  const keys = Object.keys(localStorage).filter(k => k.startsWith("chatgpt-tristan:")).sort().reverse();
  if (!keys.length) {
    root.innerHTML = `<p class="note">Aucune session locale pour l’instant.</p>`;
    return;
  }
  keys.slice(0, 12).forEach((key) => {
    const payload = JSON.parse(localStorage.getItem(key));
    const row = document.createElement("div");
    row.className = "session-row";
    row.innerHTML = `<span><strong>${payload.title || "Session"}</strong><br><small>${payload.saved_at || ""}</small></span><span><button>Charger</button> <button data-delete="1">×</button></span>`;
    row.querySelector("button").addEventListener("click", () => applySession(payload));
    row.querySelector("[data-delete]").addEventListener("click", () => { localStorage.removeItem(key); renderSessions(); });
    root.appendChild(row);
  });
}

function downloadText(filename, text) {
  const blob = new Blob([text], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function commandPreset(command) {
  const presets = {
    github: ["github-builder", "code complet + tests + workflow", "Créer ou améliorer une brique dans mon GitHub avec fichiers, tests, workflow CI, docs et runbook."],
    publication: ["publication-atlas", "publication package + professor fit", "Générer un package de publication Tristan pour universités/professeurs/recherches avec frontière OAK et review-only."],
    data: ["data-harvester", "dataset harvester + benchmark", "Chercher, télécharger de façon bornée et manifester des datasets open-source pour une théorie Tristan."],
    proof: ["math-proof", "théorie mathématique + preuves/prototypes", "Formaliser une théorie Tristan avec définitions, théorèmes, preuves partielles, contre-exemples et prototypes."],
    spectro: ["spectro-lab", "article scientifique + plan OAK", "Construire un benchmark FFWT/HAC/CVCD pour spectroscopie avec dataset, baseline et métriques."],
  };
  const p = presets[command];
  if (!p) return;
  state.mode = p[0];
  $("outputMode").value = p[1];
  $("mission").value = p[2];
  renderAll();
}

function renderAll() {
  renderModes();
  renderChips();
  renderChecks("branchList", data.branches, state.branches);
  renderChecks("actionList", data.actions, state.actions);
  renderChecks("qualityList", data.quality, state.quality);
  oakButtons();
  updatePrompt();
  renderSessions();
}

["sessionTitle", "mission", "outputMode", "constraints"].forEach((id) => $(id).addEventListener("input", updatePrompt));
$("copyPrompt").addEventListener("click", async () => {
  await navigator.clipboard.writeText($("promptOutput").value);
  toast("Prompt copié pour ChatGPT");
});
$("newSession").addEventListener("click", () => {
  $("sessionTitle").value = "Ω-SAGE Session";
  $("mission").value = "Développer une branche de l’écosystème Tristan avec rigueur OAK, prototypes, fichiers GitHub et plans de validation.";
  renderAll();
});
$("saveSession").addEventListener("click", saveSession);
$("exportSession").addEventListener("click", () => downloadText("chatgpt-tristan-session.json", JSON.stringify(sessionPayload(), null, 2)));
$("importSession").addEventListener("change", async (event) => {
  const file = event.target.files?.[0];
  if (!file) return;
  applySession(JSON.parse(await file.text()));
  toast("Session importée");
});
document.querySelectorAll("[data-command]").forEach(btn => btn.addEventListener("click", () => commandPreset(btn.dataset.command)));
renderAll();
