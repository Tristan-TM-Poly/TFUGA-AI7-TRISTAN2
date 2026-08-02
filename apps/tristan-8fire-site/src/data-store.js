"use strict";

import { rank, scoreClaim, scoreTheory } from "./search-engine.js";

const DATASETS = Object.freeze({
  theories: "data/theories.json",
  claims: "data/claims.json",
  relations: "data/relations.json"
});

function assertArray(payload, key) {
  if (!payload || !Array.isArray(payload[key])) throw new TypeError(`Invalid ${key} dataset`);
  return payload[key];
}

async function loadJson(path) {
  const response = await fetch(path, { headers: { Accept: "application/json" }, cache: "no-cache" });
  if (!response.ok) throw new Error(`${path}: HTTP ${response.status}`);
  return response.json();
}

function averageOak(theories) {
  const keys = ["verite", "utilite", "testabilite", "simplicite", "valeur", "protection"];
  const result = Object.fromEntries(keys.map((key) => [key, 0]));
  if (!theories.length) return result;
  for (const theory of theories) for (const key of keys) result[key] += Number(theory.oak?.[key] || 0);
  for (const key of keys) result[key] = result[key] / theories.length;
  return result;
}

function countBy(items, selector) {
  const result = new Map();
  for (const item of items) {
    const values = selector(item);
    for (const value of Array.isArray(values) ? values : [values]) {
      if (value === undefined || value === null || value === "") continue;
      result.set(value, (result.get(value) || 0) + 1);
    }
  }
  return [...result.entries()].sort((a, b) => b[1] - a[1] || String(a[0]).localeCompare(String(b[0]), "fr"));
}

export class CorpusStore {
  constructor() {
    this.ready = false;
    this.meta = {};
    this.theories = [];
    this.claims = [];
    this.relations = [];
    this.theoryById = new Map();
    this.claimById = new Map();
    this.claimsByTheory = new Map();
    this.outgoing = new Map();
    this.incoming = new Map();
  }

  async load() {
    const [theoryPayload, claimPayload, relationPayload] = await Promise.all(
      Object.values(DATASETS).map(loadJson)
    );
    this.theories = assertArray(theoryPayload, "theories");
    this.claims = assertArray(claimPayload, "claims");
    this.relations = assertArray(relationPayload, "relations");
    this.meta = {
      schemaVersion: theoryPayload.schema_version,
      generatedAt: theoryPayload.generated_at,
      locale: theoryPayload.locale || "fr-CA",
      disclaimer: theoryPayload.disclaimer,
      publicationRule: theoryPayload.publication_rule
    };
    this.#index();
    this.#validateReferentialIntegrity();
    this.ready = true;
    return this;
  }

  #index() {
    this.theoryById = new Map(this.theories.map((item) => [item.id, item]));
    this.claimById = new Map(this.claims.map((item) => [item.id, item]));
    this.claimsByTheory.clear();
    this.outgoing.clear();
    this.incoming.clear();
    for (const claim of this.claims) {
      const bucket = this.claimsByTheory.get(claim.theory_id) || [];
      bucket.push(claim);
      this.claimsByTheory.set(claim.theory_id, bucket);
    }
    for (const relation of this.relations) {
      const out = this.outgoing.get(relation.source) || [];
      out.push(relation);
      this.outgoing.set(relation.source, out);
      const incoming = this.incoming.get(relation.target) || [];
      incoming.push(relation);
      this.incoming.set(relation.target, incoming);
    }
  }

  #validateReferentialIntegrity() {
    const problems = [];
    for (const claim of this.claims) {
      if (!this.theoryById.has(claim.theory_id)) problems.push(`Claim ${claim.id} references missing ${claim.theory_id}`);
    }
    for (const relation of this.relations) {
      if (!this.theoryById.has(relation.source)) problems.push(`Relation ${relation.id} missing source ${relation.source}`);
      if (!this.theoryById.has(relation.target)) problems.push(`Relation ${relation.id} missing target ${relation.target}`);
    }
    if (problems.length) throw new Error(problems.slice(0, 12).join("\n"));
  }

  getTheory(id) { return this.theoryById.get(id) || null; }
  getClaim(id) { return this.claimById.get(id) || null; }
  getClaimsForTheory(id) { return [...(this.claimsByTheory.get(id) || [])]; }
  getOutgoing(id) { return [...(this.outgoing.get(id) || [])]; }
  getIncoming(id) { return [...(this.incoming.get(id) || [])]; }

  getNeighbors(id) {
    const result = new Map();
    for (const relation of this.getOutgoing(id)) result.set(relation.target, { theory: this.getTheory(relation.target), relation, direction: "out" });
    for (const relation of this.getIncoming(id)) if (!result.has(relation.source)) result.set(relation.source, { theory: this.getTheory(relation.source), relation, direction: "in" });
    return [...result.values()].filter((entry) => entry.theory);
  }

  searchTheories(query, filters = {}) {
    const ranked = rank(this.theories, query, scoreTheory);
    return ranked.filter(({ item }) => {
      if (filters.maturity && item.maturity !== filters.maturity) return false;
      if (filters.family && item.family !== filters.family) return false;
      if (filters.domain && !item.domains?.includes(filters.domain)) return false;
      if (filters.risk && !item.risks?.includes(filters.risk)) return false;
      if (filters.publicationReady === true) {
        const gate = item.publication || {};
        if (!(gate.oak_gate && gate.ip_gate && gate.privacy_gate && gate.security_gate)) return false;
      }
      return true;
    });
  }

  searchClaims(query, filters = {}) {
    const ranked = rank(this.claims, query, (claim, q) => scoreClaim(claim, q, this.getTheory(claim.theory_id)));
    return ranked.filter(({ item }) => {
      if (filters.theory && item.theory_id !== filters.theory) return false;
      if (filters.kind && item.kind !== filters.kind) return false;
      if (filters.status && item.status !== filters.status) return false;
      if (filters.risk && !item.risk_tags?.includes(filters.risk)) return false;
      return true;
    });
  }

  statistics() {
    const publicationReady = this.theories.filter((item) => {
      const gate = item.publication || {};
      return gate.oak_gate && gate.ip_gate && gate.privacy_gate && gate.security_gate;
    }).length;
    const negativeSignals = this.theories.filter((item) => /n[’']a pas|échec|limite|insuffisant|aucune supériorité|non prouv/i.test(item.status_note || "")).length;
    return {
      theories: this.theories.length,
      claims: this.claims.length,
      relations: this.relations.length,
      artifacts: this.theories.reduce((sum, item) => sum + Number(item.artifacts || 0), 0),
      publicationReady,
      negativeSignals,
      maturity: countBy(this.theories, (item) => item.maturity),
      families: countBy(this.theories, (item) => item.family),
      domains: countBy(this.theories, (item) => item.domains || []),
      claimKinds: countBy(this.claims, (item) => item.kind),
      claimStatuses: countBy(this.claims, (item) => item.status),
      relationKinds: countBy(this.relations, (item) => item.kind),
      risks: countBy(this.theories, (item) => item.risks || []),
      averageOak: averageOak(this.theories)
    };
  }

  mostConnected(limit = 12) {
    return this.theories
      .map((theory) => ({ theory, degree: this.getOutgoing(theory.id).length + this.getIncoming(theory.id).length }))
      .sort((a, b) => b.degree - a.degree || a.theory.title.localeCompare(b.theory.title, "fr"))
      .slice(0, limit);
  }

  roadmap() {
    const maturityOrder = { prototype: 0, architecture: 1, hypothèse: 2 };
    return this.theories
      .map((theory) => ({
        theory,
        action: theory.next_action,
        priority: (Number(theory.oak?.utilite || 0) + Number(theory.oak?.testabilite || 0) + Number(theory.oak?.valeur || 0)) / 3,
        maturityRank: maturityOrder[theory.maturity] ?? 3
      }))
      .sort((a, b) => b.priority - a.priority || a.maturityRank - b.maturityRank);
  }
}
