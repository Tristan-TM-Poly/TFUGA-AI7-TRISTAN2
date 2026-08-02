"use strict";

export function normalizeText(value) {
  return String(value ?? "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9ω²∞+-]+/g, " ")
    .trim();
}

export function tokenize(value) {
  return [...new Set(normalizeText(value).split(/\s+/).filter((token) => token.length > 1))];
}

function fieldScore(text, tokens, weight) {
  const normalized = normalizeText(text);
  if (!normalized) return 0;
  let score = 0;
  for (const token of tokens) {
    if (normalized === token) score += 8 * weight;
    else if (normalized.startsWith(token)) score += 5 * weight;
    else if (normalized.includes(` ${token} `)) score += 3.5 * weight;
    else if (normalized.includes(token)) score += 2 * weight;
  }
  return score;
}

export function scoreTheory(theory, query) {
  const tokens = tokenize(query);
  if (!tokens.length) return 1;
  return (
    fieldScore(theory.symbol, tokens, 2.4) +
    fieldScore(theory.title, tokens, 2.2) +
    fieldScore(theory.id, tokens, 2) +
    fieldScore(theory.summary, tokens, 1.4) +
    fieldScore(theory.domains?.join(" "), tokens, 1.3) +
    fieldScore(theory.keywords?.join(" "), tokens, 1.2) +
    fieldScore(theory.status_note, tokens, 0.9) +
    fieldScore(theory.next_action, tokens, 0.9)
  );
}

export function scoreClaim(claim, query, theory) {
  const tokens = tokenize(query);
  if (!tokens.length) return 1;
  return (
    fieldScore(claim.id, tokens, 2.1) +
    fieldScore(claim.title, tokens, 2) +
    fieldScore(claim.statement, tokens, 1.6) +
    fieldScore(claim.kind, tokens, 1.4) +
    fieldScore(claim.status, tokens, 1.2) +
    fieldScore(claim.epistemic_level, tokens, 1.2) +
    fieldScore(claim.risk_tags?.join(" "), tokens, 1) +
    fieldScore(claim.falsification_or_limit, tokens, 0.9) +
    fieldScore(claim.next_test, tokens, 0.9) +
    fieldScore(theory?.title, tokens, 1.2) +
    fieldScore(theory?.symbol, tokens, 1.4)
  );
}

export function rank(items, query, scorer, limit = Infinity) {
  return items
    .map((item) => ({ item, score: scorer(item, query) }))
    .filter((entry) => entry.score > 0)
    .sort((a, b) => b.score - a.score || String(a.item.title).localeCompare(String(b.item.title), "fr"))
    .slice(0, limit);
}
