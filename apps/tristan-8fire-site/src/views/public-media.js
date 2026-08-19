"use strict";

import {
  COGNITIVE_MEDIA_ISA,
  PUBLIC_MEDIA_CONSTITUTION,
  RADIO_CANADA_MRU,
  compileBroadcastableKnowledgeObject,
  mediaOakGate,
  publicMediaReceipt,
  semanticTranscode
} from "../public-media-kernel.js";

function el(tag, attrs = {}, children = []) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (key === "className") node.className = value;
    else if (key === "text") node.textContent = value;
    else if (key.startsWith("data-")) node.setAttribute(key, value);
    else if (value !== undefined && value !== null) node.setAttribute(key, value);
  }
  for (const child of Array.isArray(children) ? children : [children]) if (child) node.append(child);
  return node;
}

function card(title, body, status = "") {
  return el("article", { className: `pm-card ${status}`.trim() }, [
    el("h3", { text: title }),
    ...(Array.isArray(body) ? body : [el("p", { text: String(body) })])
  ]);
}

function meter(label, value, note) {
  const pct = `${Math.round(value * 100)}%`;
  return el("article", { className: "pm-meter" }, [
    el("span", { text: label }),
    el("strong", { text: pct }),
    el("div", { className: "pm-bar", role: "meter", "aria-valuemin": "0", "aria-valuemax": "100", "aria-valuenow": String(Math.round(value * 100)) }, [
      el("i", { style: `width:${pct}` })
    ]),
    el("small", { text: note })
  ]);
}

function demoAsset() {
  return {
    evidenceLevel: "PROTOTYPE",
    demonstrability: 0.86,
    visualPower: 0.82,
    publicRelevance: 0.90,
    clarity: 0.88,
    timeliness: 0.55,
    reproducibility: 0.74,
    rightsReadiness: 0.95,
    correctionCapacity: 0.80,
    requestedReach: 0.30
  };
}

function renderWorkspace() {
  const mru = RADIO_CANADA_MRU;
  return el("section", { className: "pm-section" }, [
    el("div", { className: "pm-section-head" }, [
      el("div", {}, [el("p", { className: "eyebrow", text: mru.id }), el("h2", { text: mru.title })]),
      el("span", { className: "pm-badge hold", text: "PROTOTYPE · NO AFFILIATION" })
    ]),
    el("p", { className: "pm-affiliation", text: mru.affiliation }),
    el("p", { className: "pm-question", text: mru.question }),
    el("div", { className: "pm-grid" }, [
      card("Claims", mru.claims.map((claim) => el("p", {}, [el("code", { text: claim.id }), document.createTextNode(` ${claim.label} — ${claim.status}`)]))),
      card("Timeline", mru.timeline.map(([id, label]) => el("p", {}, [el("code", { text: id }), document.createTextNode(` ${label}`)]))),
      card("What remains unknown", el("ul", {}, mru.unknowns.map((item) => el("li", { text: item }))))
    ])
  ]);
}

function renderCompiler() {
  const bko = compileBroadcastableKnowledgeObject({
    title: "Evidence-aware public story",
    question: RADIO_CANADA_MRU.question,
    evidenceLevel: "PROTOTYPE",
    evidence: ["Prototype kernel", "Focused automated tests"],
    limitations: RADIO_CANADA_MRU.unknowns,
    provenance: ["Tristan Web OS branch / PR history"],
    attribution: ["Tristan-TM-Poly"],
    correctionEndpoint: "GitHub issue / PR review"
  });
  const transcode = semanticTranscode(bko, 60);
  const gate = mediaOakGate({
    evidenceLevel: bko.evidenceLevel,
    question: bko.question,
    evidence: bko.evidence.length,
    limitations: bko.limitations.length,
    provenance: bko.provenance.length,
    rights: true,
    correctionEndpoint: bko.correctionEndpoint,
    humanEditorialReview: true,
    autoPublish: false,
    claimsProof: false
  });

  return el("section", { className: "pm-section" }, [
    el("div", { className: "pm-section-head" }, [
      el("div", {}, [el("p", { className: "eyebrow", text: "KNOWLEDGE IR → MEDIA" }), el("h2", { text: "Broadcastable Knowledge Object" })]),
      el("span", { className: `pm-badge ${gate.status === "HOLD" ? "hold" : "pass"}`, text: gate.status })
    ]),
    el("div", { className: "pm-compiler" }, [
      el("pre", {}, [el("code", { text: "QUESTION\n  ↓\nEVIDENCE KERNEL\n  ↓\nOAK / RIGHTS / IP\n  ↓\nKNOWLEDGE IR\n  ↓\nMEDIA GENOME\n  ↓\nHUMAN EDITORIAL REVIEW" })]),
      el("div", {}, [
        el("p", {}, [el("strong", { text: bko.id }), document.createTextNode(` · ${bko.evidenceLevel}`)]),
        el("p", { text: `60 s transcode: ${transcode.status}` }),
        el("p", { text: `Formats candidats: ${bko.mediaGenome.length}` }),
        el("p", { text: "Publication automatique: interdite" })
      ])
    ])
  ]);
}

function renderReadiness() {
  const receipt = publicMediaReceipt(demoAsset());
  const d = receipt.readiness.dimensions;
  return el("section", { className: "pm-section" }, [
    el("div", { className: "pm-section-head" }, [
      el("div", {}, [el("p", { className: "eyebrow", text: "GO MEDIA PR MAX" }), el("h2", { text: "Evidence × démonstration × valeur publique" })]),
      el("strong", { className: "pm-score", text: `${Math.round(receipt.readiness.score * 100)}/100` })
    ]),
    el("div", { className: "pm-meters" }, [
      meter("Evidence", d.evidence, receipt.readiness.evidenceLevel),
      meter("Démonstrabilité", d.demonstrability, "Peut-on montrer quelque chose ?"),
      meter("Clarté", d.clarity, "Compréhensible sans le corpus complet"),
      meter("Reproductibilité", d.reproducibility, "Artifact + test + baseline"),
      meter("Droits", d.rightsReadiness, "RightsGate prêt")
    ]),
    el("p", { className: "fineprint", text: `Amplification autorisée (normalisée): ${receipt.amplification.allowedReach}. Vagues éligibles: ${receipt.eligibleWaves.join(", ") || "aucune"}. Ce score est un signal de préparation, pas une mesure de vérité ou une décision éditoriale.` })
  ]);
}

function renderConstitution() {
  return el("section", { className: "pm-section pm-two" }, [
    el("div", {}, [
      el("p", { className: "eyebrow", text: "CONSTITUTION OAK-RC / PUBLIC MEDIA" }),
      el("h2", { text: "La portée ne doit jamais dépasser la capacité de corriger" }),
      el("ul", { className: "pm-laws" }, PUBLIC_MEDIA_CONSTITUTION.map((law) => el("li", { text: law })))
    ]),
    el("div", {}, [
      el("p", { className: "eyebrow", text: "COGNITIVE MEDIA ISA" }),
      el("h2", { text: "Une grammaire, plusieurs médias" }),
      el("div", { className: "pm-isa" }, COGNITIVE_MEDIA_ISA.map((op) => el("code", { text: op }))),
      el("p", { className: "fineprint", text: "Vidéo, article, radio et interface deviennent des rendus différents d'un même Knowledge Transformation Program." })
    ])
  ]);
}

export function renderPublicMedia() {
  const root = el("div", { className: "pm-page" });
  root.append(
    el("section", { className: "pm-hero" }, [
      el("p", { className: "eyebrow", text: "GO PR MAX × GO TRISTAN × GO TRISTAN2 × GO TRISTAN² × MULTI-MERGE-MAX" }),
      el("h1", { text: "Public Media Lab" }),
      el("p", { className: "pm-lede", text: "Transformer une création en objet culturel vérifiable, transmissible et corrigeable — sans automatiser l'autorité éditoriale." }),
      el("code", { className: "pm-equation", text: "QUESTION → TEST → CRYSTALLIZE → TRANSCODE → OAK → ROUTE → DIFFUSE → CRITIQUE → REGENERATE" })
    ]),
    renderWorkspace(),
    renderReadiness(),
    renderCompiler(),
    renderConstitution(),
    el("section", { className: "pm-section pm-boundary" }, [
      el("p", { className: "eyebrow", text: "OAK CLAIM BOUNDARY" }),
      el("h2", { text: "Prototype de recherche et d'interface, pas proposition institutionnelle approuvée" }),
      el("p", { text: "Cette vue matérialise une architecture Tristan pour média public. Elle ne prétend ni partenariat avec Radio-Canada, ni bénéfice mesuré, ni validation éditoriale, ni preuve scientifique de ses métriques. La prochaine étape OAK est une expérience utilisateur comparative sur un dossier public avec revue humaine." })
    ])
  );
  return root;
}
