/* ChatGPT Tristan OS v2.4 addons: Virtual Universities / Institution Genesis local cockpit. */
(function () {
  const $ = (id) => document.getElementById(id);
  const storageKey = "chatgpt-tristan-v2:virtualUniversity";
  const selectedAgents = new Set(["Tristan-Professor", "Tristan-Socratic", "Tristan-Lab", "Tristan-OAK"]);
  const agentCatalog = [
    "Tristan-Professor",
    "Tristan-Socratic",
    "Tristan-Lab",
    "Tristan-Researcher",
    "Tristan-Engineer",
    "Tristan-Critic",
    "Tristan-OAK",
    "Tristan-Mentor",
    "Tristan-CurriculumCompiler",
    "Tristan-GameMaster"
  ];

  function uid(prefix) {
    if (globalThis.crypto && typeof globalThis.crypto.randomUUID === "function") {
      return `${prefix}-${globalThis.crypto.randomUUID()}`;
    }
    return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  }

  function toast(message) {
    const box = $("toast");
    if (!box) return;
    box.textContent = message;
    box.classList.add("show");
    setTimeout(() => box.classList.remove("show"), 1800);
  }

  function currentGenome() {
    try { return JSON.parse(localStorage.getItem(storageKey) || "null"); }
    catch (_) { return null; }
  }

  function persist(genome) {
    localStorage.setItem(storageKey, JSON.stringify(genome, null, 2));
    renderReport(genome);
  }

  function governanceFor(riskTier) {
    const common = [
      "Agent != Human",
      "Capability != Authority",
      "Reputation != Evidence",
      "Simulation != Reality",
      "Generated != Verified",
      "LocalPASS != GlobalPASS"
    ];
    if (riskTier === "high") {
      common.push("Sensitive or irreversible actions require explicit human approval");
      common.push("Independent verification required before promotion");
    }
    return common;
  }

  function buildGenome(parent) {
    const now = new Date().toISOString();
    const name = ($("universityName")?.value || "Université Virtuelle Tristan").trim();
    const mission = ($("universityMission")?.value || "Apprendre, rechercher et construire avec preuves.").trim();
    const visibility = $("universityMode")?.value || "invite";
    const riskTier = $("universityRisk")?.value || "medium";
    const maxMembers = Math.max(2, Math.min(512, Number($("universityCapacity")?.value || 32)));
    const id = uid("uni");
    return {
      version: "omega-virtual-university-genome.v0.1",
      institution_type: "virtual_university",
      id,
      lineage: parent ? { parent_id: parent.id, operation: "fork", forked_at: now } : null,
      name: parent ? `${name} — Fork` : name,
      mission,
      visibility,
      created_at: now,
      lifecycle: { status: "sandbox", cycle: 0, can_dissolve: true, can_fork: true, can_merge_propose: true },
      multiplayer: {
        contract_status: "prototype_only",
        room_id: uid("room"),
        max_members: maxMembers,
        authenticated_members_required: true,
        realtime_backend_required: true,
        members: [{ principal: "local-subscriber", role: "founder", status: "local-placeholder" }]
      },
      agents: [...selectedAgents].map((name) => ({ name, identity: "AI agent/persona", authority: "bounded", status: "sandbox" })),
      curriculum: { strategy: "capability_geodesic", quests: [], mastery_evidence_required: true },
      research: { labs: [], claims: [], counterexample_search_required: true },
      governance: {
        risk_tier: riskTier,
        constitution: governanceFor(riskTier),
        permission_model: "capability-based + explicit approval gates",
        sanctions_from_single_classifier_forbidden: true
      },
      economy: { mode: "internal-contribution-ledger", real_money_actions: "disabled_without_explicit_authorization" },
      evidence: [],
      metrics: { verified_capability: 0, simulated_capability: 0, evidence_count: 0, coordination_debt: 0, epistemic_debt: 0 },
      oak: {
        status: "OAK-3 scaffold",
        blockers: ["real authenticated multiplayer backend", "persistent server-side storage", "independent real-user validation"],
        boundary: "Local simulation is not evidence that multiplayer, learning outcomes, or institutional performance work in production."
      }
    };
  }

  function renderAgents() {
    const root = $("universityAgents");
    if (!root) return;
    root.innerHTML = "";
    agentCatalog.forEach((agent) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = `chip ${selectedAgents.has(agent) ? "active" : ""}`;
      button.textContent = agent;
      button.addEventListener("click", () => {
        if (selectedAgents.has(agent)) selectedAgents.delete(agent); else selectedAgents.add(agent);
        renderAgents();
      });
      root.appendChild(button);
    });
  }

  function renderReport(genome) {
    const report = $("universityReport");
    if (!report) return;
    if (!genome) {
      report.textContent = "Aucune université locale. Génère un UniversityGenome pour commencer.";
      return;
    }
    report.textContent = JSON.stringify(genome, null, 2);
  }

  function generateUniversity() {
    const genome = buildGenome(null);
    persist(genome);
    toast("UniversityGenome généré en sandbox");
  }

  function simulateCycle() {
    const genome = currentGenome() || buildGenome(null);
    genome.lifecycle.cycle += 1;
    const cycle = genome.lifecycle.cycle;
    const agentFactor = Math.min(6, genome.agents.length);
    const simulatedGain = 2 + agentFactor + (cycle % 3);
    genome.metrics.simulated_capability += simulatedGain;
    genome.metrics.evidence_count += 1;
    genome.metrics.epistemic_debt += 1;
    genome.evidence.push({
      id: uid("receipt"),
      created_at: new Date().toISOString(),
      epistemic_type: "SIMULATED",
      claim: `Sandbox cycle ${cycle} completed`,
      value: simulatedGain,
      falsifier: "Real authenticated cohort fails to reproduce the expected capability gain",
      provenance: "local v2.4 deterministic sandbox",
      promotion_allowed: false
    });
    genome.oak.status = "OAK-4 local prototype";
    persist(genome);
    toast("Cycle simulé — pas une validation réelle");
  }

  function forkUniversity() {
    const parent = currentGenome();
    if (!parent) {
      toast("Génère d'abord une université");
      return;
    }
    const fork = buildGenome(parent);
    fork.evidence.push({
      id: uid("receipt"),
      created_at: new Date().toISOString(),
      epistemic_type: "DERIVED",
      claim: "Fork lineage created from local parent genome",
      provenance: parent.id,
      promotion_allowed: false
    });
    persist(fork);
    if ($("universityName")) $("universityName").value = fork.name;
    toast("Fork institutionnel créé");
  }

  function buildBackendPrompt() {
    const genome = currentGenome() || buildGenome(null);
    const prompt = [
      "# Ω-VIRTUAL-UNIVERSITIES-T∞ — Production multiplayer implementation",
      "",
      "Implement this UniversityGenome as a production-capable, authenticated multiplayer feature.",
      "",
      JSON.stringify(genome, null, 2),
      "",
      "## Required production layers",
      "- Subscriber authentication and tenant isolation.",
      "- Persistent server-side UniversityGenome / InstitutionState storage.",
      "- Realtime room presence and events (WebSocket/SSE or equivalent).",
      "- Capability-based RBAC and explicit approval gates.",
      "- Tristan Virtual agent router with clear AI identity labels.",
      "- Evidence ledger with epistemic types and immutable provenance records.",
      "- Fork / merge-proposal / rollback semantics.",
      "- Compute quotas, rate limits, cost guards and abuse protection.",
      "- OAK checks: Generated != Verified; Simulation != Reality; Agent != Human.",
      "- Tests for tenant isolation, permissions, race conditions, replay/idempotency and export/delete flows.",
      "",
      "Do not claim the local prototype already provides multiplayer. Produce a reversible PR and tests before deployment."
    ].join("\n");
    if ($("prompt")) $("prompt").value = prompt;
    if ($("universityReport")) $("universityReport").textContent = prompt;
    toast("Prompt backend compilé");
  }

  function exportUniversity() {
    const genome = currentGenome();
    if (!genome) {
      toast("Aucune université à exporter");
      return;
    }
    const blob = new Blob([JSON.stringify(genome, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${genome.id}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  function resetUniversity() {
    localStorage.removeItem(storageKey);
    renderReport(null);
    toast("Sandbox université réinitialisée");
  }

  function wire() {
    renderAgents();
    renderReport(currentGenome());
    const actions = {
      generateUniversity,
      simulateUniversity: simulateCycle,
      forkUniversity,
      buildUniversityBackendPrompt: buildBackendPrompt,
      exportUniversity,
      resetUniversity
    };
    Object.entries(actions).forEach(([id, fn]) => {
      const node = $(id);
      if (node) node.addEventListener("click", fn);
    });
  }

  wire();
})();
