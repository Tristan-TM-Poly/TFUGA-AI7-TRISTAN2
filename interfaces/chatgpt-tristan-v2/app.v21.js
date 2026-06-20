/* ChatGPT Tristan OS v2.1 addons: prompt diff, safety radar, canonizer. */
(function () {
  const $ = (id) => document.getElementById(id);
  const localKey = "chatgpt-tristan-v2:lastPromptSnapshot";

  function toast(message) {
    const box = $("toast");
    if (!box) return;
    box.textContent = message;
    box.classList.add("show");
    setTimeout(() => box.classList.remove("show"), 1800);
  }

  function currentPrompt() {
    if (typeof compile === "function") return compile();
    return $("prompt")?.value || "";
  }

  function snapshotPrompt() {
    localStorage.setItem(localKey, currentPrompt());
    $("promptDiff").textContent = "Snapshot saved. Modify the session, then click Compare prompt.";
    toast("Snapshot prompt sauvé");
  }

  function diffPrompt() {
    const before = (localStorage.getItem(localKey) || "").split(/\r?\n/);
    const after = currentPrompt().split(/\r?\n/);
    const beforeSet = new Set(before.filter(Boolean));
    const afterSet = new Set(after.filter(Boolean));
    const added = after.filter((line) => line && !beforeSet.has(line)).slice(0, 80);
    const removed = before.filter((line) => line && !afterSet.has(line)).slice(0, 80);
    const lines = ["# Prompt Diff", "", "## Added", ...(added.length ? added.map((x) => "+ " + x) : ["none"]), "", "## Removed", ...(removed.length ? removed.map((x) => "- " + x) : ["none"])];
    $("promptDiff").textContent = lines.join("\n");
    toast("Diff généré");
  }

  function safetyRadar() {
    const prompt = currentPrompt().toLowerCase();
    const checks = [
      ["OAK boundary", prompt.includes("oak")],
      ["M− negative memory", prompt.includes("m−") || prompt.includes("negative")],
      ["No future promise", prompt.includes("produire maintenant") || prompt.includes("ne pas promettre")],
      ["No automatic outreach", !prompt.includes("envoyer automatiquement") && !prompt.includes("mass email")],
      ["Claim distinction", prompt.includes("vision") && prompt.includes("preuve")],
      ["GitHub verification", prompt.includes("fetch_file") || !prompt.includes("github")],
      ["Data license caution", prompt.includes("licence") || !prompt.includes("data")],
      ["Publication endorsement caution", prompt.includes("endorsement") || !prompt.includes("publication")]
    ];
    const score = checks.filter(([, ok]) => ok).length;
    const report = {
      version: "chatgpt-tristan-safety-radar.v1",
      score,
      max_score: checks.length,
      status: score >= 7 ? "strong" : score >= 5 ? "promising" : "needs_attention",
      checks: checks.map(([name, ok]) => ({ name, ok })),
      residues: checks.filter(([, ok]) => !ok).map(([name]) => "missing_or_weak_" + name.toLowerCase().replace(/[^a-z0-9]+/g, "_"))
    };
    $("safetyReport").textContent = JSON.stringify(report, null, 2);
    toast("Safety radar terminé");
  }

  function canonizeSession() {
    const session = typeof payload === "function" ? payload() : { prompt: currentPrompt() };
    const title = session.title || "Untitled session";
    const canon = {
      version: "chatgpt-tristan-canon-entry.v1",
      name: title,
      mode: session.mode,
      oak_target: session.oak_target,
      artifact_intent: session.intent,
      branches: session.branches || [],
      positive_memory: session.positive_memory || [],
      negative_memory: session.negative_memory || [],
      oak_cards: session.claims || [],
      hgfm_node: {
        id: title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "session",
        type: "chatgpt_tristan_session",
        links: ["mission", "oak", "memory", "artifact", "validation"]
      },
      next_actions: [
        "review generated prompt",
        "run safety radar",
        "promote only after testable artifact",
        "export JSON before major changes"
      ],
      boundary: {
        no_official_chatgpt_modification_claim: true,
        human_review_for_external_action: true,
        fertility_is_not_proof: true
      }
    };
    $("safetyReport").textContent = JSON.stringify(canon, null, 2);
    localStorage.setItem("chatgpt-tristan-v2:lastCanonEntry", JSON.stringify(canon, null, 2));
    toast("Session canonisée");
  }

  function wire() {
    const snapshot = $("snapshotPrompt");
    const diff = $("diffPrompt");
    const radar = $("safetyRadar");
    const canon = $("canonizeSession");
    if (snapshot) snapshot.onclick = snapshotPrompt;
    if (diff) diff.onclick = diffPrompt;
    if (radar) radar.onclick = safetyRadar;
    if (canon) canon.onclick = canonizeSession;
  }

  wire();
})();
