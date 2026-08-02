"use strict";

function download(name, content, type) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = name;
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function quoteCsv(value) {
  const text = String(value ?? "");
  return /[",\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

export function exportJson(name, value) {
  download(name, `${JSON.stringify(value, null, 2)}\n`, "application/json;charset=utf-8");
}

export function exportTheoriesCsv(theories) {
  const headers = ["id", "symbol", "title", "maturity", "evidence", "family", "domains", "artifacts", "next_action", "source_path"];
  const lines = [headers.join(",")];
  for (const item of theories) {
    lines.push(headers.map((key) => quoteCsv(key === "domains" ? item.domains?.join(" | ") : item[key])).join(","));
  }
  download("tristan-web-os-theories.csv", `${lines.join("\n")}\n`, "text/csv;charset=utf-8");
}

export function exportClaimsCsv(claims) {
  const headers = ["id", "theory_id", "kind", "status", "epistemic_level", "title", "statement", "falsification_or_limit", "next_test"];
  const lines = [headers.join(",")];
  for (const item of claims) lines.push(headers.map((key) => quoteCsv(item[key])).join(","));
  download("tristan-web-os-claims.csv", `${lines.join("\n")}\n`, "text/csv;charset=utf-8");
}

export function exportTheoryMarkdown(theory, claims, neighbors) {
  const oak = Object.entries(theory.oak || {}).map(([key, value]) => `- ${key}: ${Number(value).toFixed(2)}`).join("\n");
  const claimText = claims.map((claim) => [
    `### ${claim.title}`,
    "",
    `- ID: \`${claim.id}\``,
    `- Statut: ${claim.status}`,
    `- Niveau: ${claim.epistemic_level}`,
    "",
    claim.statement,
    "",
    `**Limite / falsification :** ${claim.falsification_or_limit}`,
    "",
    `**Prochain test :** ${claim.next_test}`
  ].join("\n")).join("\n\n");
  const relationText = neighbors.map(({ theory: target, relation, direction }) =>
    `- ${direction === "out" ? "→" : "←"} **${target.symbol}** — ${relation.kind}: ${relation.rationale}`
  ).join("\n");
  const markdown = [
    `# ${theory.symbol} — ${theory.title}`,
    "",
    theory.summary,
    "",
    `- Maturité: ${theory.maturity}`,
    `- Preuve: ${theory.evidence}`,
    `- Famille: ${theory.family}`,
    `- Domaines: ${(theory.domains || []).join(", ")}`,
    `- Version: ${theory.version}`,
    `- Source: \`${theory.source_path}\``,
    "",
    "## État OAK",
    "",
    theory.status_note,
    "",
    oak,
    "",
    "## Prochaine action",
    "",
    theory.next_action,
    "",
    "## Claims",
    "",
    claimText || "Aucun claim.",
    "",
    "## Relations de navigation",
    "",
    relationText || "Aucune relation.",
    "",
    "> Les relations sont des aides de navigation et non des preuves causales."
  ].join("\n");
  download(`${theory.id}.md`, `${markdown}\n`, "text/markdown;charset=utf-8");
}

export function exportGraphml(theories, relations) {
  const esc = (value) => String(value ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll('"', "&quot;");
  const nodes = theories.map((item) => `    <node id="${esc(item.id)}"><data key="title">${esc(item.title)}</data><data key="symbol">${esc(item.symbol)}</data><data key="maturity">${esc(item.maturity)}</data></node>`).join("\n");
  const edges = relations.map((item) => `    <edge id="${esc(item.id)}" source="${esc(item.source)}" target="${esc(item.target)}"><data key="kind">${esc(item.kind)}</data><data key="strength">${esc(item.strength)}</data></edge>`).join("\n");
  const xml = `<?xml version="1.0" encoding="UTF-8"?>\n<graphml xmlns="http://graphml.graphdrawing.org/xmlns">\n  <key id="title" for="node" attr.name="title" attr.type="string"/>\n  <key id="symbol" for="node" attr.name="symbol" attr.type="string"/>\n  <key id="maturity" for="node" attr.name="maturity" attr.type="string"/>\n  <key id="kind" for="edge" attr.name="kind" attr.type="string"/>\n  <key id="strength" for="edge" attr.name="strength" attr.type="double"/>\n  <graph id="tristan-web-os" edgedefault="directed">\n${nodes}\n${edges}\n  </graph>\n</graphml>\n`;
  download("tristan-web-os.graphml", xml, "application/graphml+xml;charset=utf-8");
}
