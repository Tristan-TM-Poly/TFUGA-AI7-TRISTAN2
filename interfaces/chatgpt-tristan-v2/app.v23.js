/* ChatGPT Tristan OS v2.3 addons: local score history and dashboard prompt. */
(function () {
  const $ = (id) => document.getElementById(id);
  const key = "chatgpt-tristan-v2:scoreHistory";

  function toast(message) {
    const box = $("toast");
    if (!box) return;
    box.textContent = message;
    box.classList.add("show");
    setTimeout(() => box.classList.remove("show"), 1800);
  }

  function loadHistory() {
    try { return JSON.parse(localStorage.getItem(key) || "[]"); }
    catch (_) { return []; }
  }

  function saveHistory(records) {
    localStorage.setItem(key, JSON.stringify(records, null, 2));
  }

  function currentEstimate() {
    const raw = localStorage.getItem("chatgpt-tristan-v2:lastImpactEstimate");
    if (raw) return JSON.parse(raw);
    return { heuristic_score: 70, rating: "very_strong", boundary: "fallback heuristic" };
  }

  function addLocalScore() {
    const records = loadHistory();
    const estimate = currentEstimate();
    records.push({
      version: "chatgpt-tristan-v2.3-local-score.v1",
      created_at: new Date().toISOString(),
      score: estimate.heuristic_score || estimate.score || 0,
      rating: estimate.rating || "unknown",
      source: "local_ui_estimate",
      boundary: "heuristic only, not validation"
    });
    saveHistory(records);
    renderScoreHistory();
    toast("Score ajouté à l'historique local");
  }

  function renderScoreHistory() {
    const records = loadHistory();
    if (!records.length) {
      $("scoreHistoryReport").textContent = "No local score history yet. Estimate impact first, then add score.";
      return;
    }
    const scores = records.map((x) => Number(x.score || 0));
    const summary = {
      version: "chatgpt-tristan-v2.3-score-history.v1",
      count: records.length,
      average: Math.round((scores.reduce((a, b) => a + b, 0) / scores.length) * 10) / 10,
      best: Math.max(...scores),
      latest: scores[scores.length - 1],
      trend: Math.round((scores[scores.length - 1] - scores[0]) * 10) / 10,
      plus_ultra_count: scores.filter((x) => x >= 81).length,
      records,
      boundary: "local process trend, not proof"
    };
    $("scoreHistoryReport").textContent = JSON.stringify(summary, null, 2);
  }

  function buildScoreHistoryPrompt() {
    const prompt = [
      "# Build Omega Response Score History",
      "",
      "Use GitHub to run or improve the score history dashboard.",
      "",
      "Expected chain:",
      "1. Collect configs/response_impact/*.json.",
      "2. Run omega_response_score_history.py.",
      "3. Produce RESPONSE_SCORE_HISTORY.md and response_score_history.json.",
      "4. Cite artifacts and provide quantitative delta.",
      "",
      "OAK boundary:",
      "- Scores are process heuristics, not proof.",
      "- Keep residues M-minus.",
      "- Compare latest score against previous iterations."
    ].join("\n");
    $("scoreHistoryReport").textContent = prompt;
    if ($("prompt")) $("prompt").value = prompt;
    toast("Prompt dashboard score généré");
  }

  function wire() {
    const add = $("addLocalScore");
    const render = $("renderScoreHistory");
    const prompt = $("buildScoreHistoryPrompt");
    if (add) add.onclick = addLocalScore;
    if (render) render.onclick = renderScoreHistory;
    if (prompt) prompt.onclick = buildScoreHistoryPrompt;
  }

  wire();
})();
