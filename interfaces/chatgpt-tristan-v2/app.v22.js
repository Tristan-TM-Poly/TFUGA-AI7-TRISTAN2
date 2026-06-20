/* ChatGPT Tristan OS v2.2 addons: iteration chain cockpit and impact estimation. */
(function () {
  const $ = (id) => document.getElementById(id);

  function toast(message) {
    const box = $("toast");
    if (!box) return;
    box.textContent = message;
    box.classList.add("show");
    setTimeout(() => box.classList.remove("show"), 1800);
  }

  function sessionPayload() {
    if (typeof payload === "function") return payload();
    return { title: $("title")?.value || "session", mode: $("mode")?.value || "unknown" };
  }

  function buildIterationChainPrompt() {
    const session = sessionPayload();
    const repo = session.repo || "Tristan-TM-Poly/TFUGA-AI7-TRISTAN2";
    const prompt = [
      "# Omega Iteration Chain Execution",
      "",
      "Repo: " + repo,
      "Session: " + (session.title || "untitled"),
      "Mode: " + (session.mode || "unknown"),
      "",
      "Execute the bounded chain:",
      "1. Generate 1024 candidates with omega_iteration_multiplier.py.",
      "2. Select a diverse batch with omega_iteration_batch_selector.py.",
      "3. Build execution pack with omega_iteration_execution_pack.py.",
      "4. Execute only a small reviewable subset.",
      "5. Analyze response impact with omega_response_impact_analyzer.py.",
      "",
      "OAK rules:",
      "- Do not execute all 1024 blindly.",
      "- Verify created files with fetch_file.",
      "- Report quantitative score after response.",
      "- Keep M-minus residues.",
      "- Prototype is not proof."
    ].join("\n");
    $("iterationChainReport").textContent = prompt;
    if ($("prompt")) $("prompt").value = prompt;
    toast("Prompt chaîne itérative généré");
  }

  function estimateImpact() {
    const session = sessionPayload();
    const branches = session.branches || [];
    const actions = session.github_actions || [];
    const claims = session.claims || [];
    const estimatedArtifacts = Math.min(12, 3 + actions.length + Math.floor(branches.length / 3) + claims.length);
    const diversity = Math.min(8, 2 + new Set(branches).size / 3 + actions.length / 2);
    const oak = (JSON.stringify(session).toLowerCase().includes("oak") ? 12 : 6) + (claims.length ? 3 : 0);
    const automation = actions.some((x) => String(x).includes("workflow")) ? 12 : 8;
    const testability = actions.some((x) => String(x).includes("test")) ? 12 : 7;
    const strategic = Math.min(12, branches.filter((b) => /OAK|HGFM|Bayes|Spectro|Publication|Data|AIT/i.test(b)).length * 1.4);
    const reuse = Math.min(10, actions.length + (branches.includes("M−") ? 2 : 0));
    const score = Math.round(Math.min(100, estimatedArtifacts * 1.5 + diversity * 2 + oak + automation + testability + strategic + reuse));
    const report = {
      version: "chatgpt-tristan-v2.2-impact-estimate.v1",
      heuristic_score: score,
      rating: score >= 81 ? "plus_ultra" : score >= 61 ? "very_strong" : score >= 41 ? "strong" : "useful",
      estimated_artifacts: estimatedArtifacts,
      diversity_estimate: Math.round(diversity * 10) / 10,
      oak_safety_estimate: oak,
      automation_estimate: automation,
      testability_estimate: testability,
      strategic_estimate: Math.round(strategic * 10) / 10,
      reuse_estimate: reuse,
      boundary: "heuristic only, not validation"
    };
    $("iterationChainReport").textContent = JSON.stringify(report, null, 2);
    localStorage.setItem("chatgpt-tristan-v2:lastImpactEstimate", JSON.stringify(report, null, 2));
    toast("Impact estimé");
  }

  function wire() {
    const chain = $("buildIterationChainPrompt");
    const impact = $("estimateImpact");
    if (chain) chain.onclick = buildIterationChainPrompt;
    if (impact) impact.onclick = estimateImpact;
  }

  wire();
})();
