"use strict";

import {
  AUDIENCE_PROFILES,
  COGNITIVE_WEB_ISA,
  WORLD_CONSTITUTION,
  WORLD_MODES,
  compileWorld,
  knowledgeWorldKernelReceipt,
  worldDiff
} from "../knowledge-world-kernel.js";

function el(tag, attrs = {}, children = []) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (key === "className") node.className = value;
    else if (key === "text") node.textContent = value;
    else if (key.startsWith("data-")) node.setAttribute(key, value);
    else if (key === "selected" || key === "disabled") node[key] = Boolean(value);
    else if (value !== undefined && value !== null) node.setAttribute(key, value);
  }
  for (const child of Array.isArray(children) ? children : [children]) if (child) node.append(child);
  return node;
}

function humanEvidence(theory = {}) {
  const maturity = String(theory.maturity || "").toLowerCase();
  if (/preuve|proven|theorem/.test(maturity)) return "PROVEN";
  if (/replic/.test(maturity)) return "REPLICATED";
  if (/mesur|measured|validated/.test(maturity)) return "MEASURED";
  if (/prototype/.test(maturity)) return "PROTOTYPE";
  if (/formal|architecture/.test(maturity)) return "FORMALIZATION";
  return "HYPOTHESIS";
}

function sourceObjects(store) {
  return store.mostConnected(7).map(({ theory, degree }) => ({
    id: theory.id,
    title: theory.title,
    evidenceLevel: humanEvidence(theory),
    kind: `THEORY · degree ${degree}`
  }));
}

function stat(label, value, note) {
  return el("article", { className: "kw-stat" }, [
    el("span", { text: label }),
    el("strong", { text: String(value) }),
    note ? el("small", { text: note }) : null
  ]);
}

function badge(text, tone = "") {
  return el("span", { className: `kw-badge ${tone}`.trim(), text });
}

function renderWorldCard(world) {
  const floorTone = world.evidencePolicy.floorSatisfied ? "pass" : "hold";
  return el("article", { className: "kw-world-card" }, [
    el("div", { className: "kw-world-head" }, [
      el("div", {}, [
        el("p", { className: "eyebrow", text: world.profile }),
        el("h3", { text: world.lens.label })
      ]),
      badge(world.evidencePolicy.floorSatisfied ? "EVIDENCE FLOOR PASS" : "EVIDENCE FLOOR HOLD", floorTone)
    ]),
    el("p", { text: `${world.lens.intent} · ${world.mode} · profondeur ${world.lens.depth}` }),
    world.lens.affiliationBoundary ? el("p", { className: "kw-boundary", text: world.lens.affiliationBoundary }) : null,
    el("div", { className: "kw-chip-row" }, world.lens.operators.slice(0, 8).map((op) => el("code", { text: op }))),
    el("p", { className: "kw-fine", text: `World ${world.id} · ${world.objects.length} objets partagés · ${world.residuals.length} résidus` })
  ]);
}

function renderReceipt(world) {
  return el("section", { className: "kw-section" }, [
    el("div", { className: "kw-section-head" }, [
      el("div", {}, [el("p", { className: "eyebrow", text: "WORLD RECEIPT" }), el("h2", { text: "Pourquoi cette vue existe" })]),
      badge(world.receipt.id)
    ]),
    el("div", { className: "kw-grid-three" }, [
      stat("Profil", world.profile, "Lentille explicite"),
      stat("Mode", world.mode, "Programme cognitif"),
      stat("Evidence", world.evidencePolicy.canonicalEvidenceLevel, world.evidencePolicy.floorSatisfied ? "Seuil audience satisfait" : `Seuil ${world.evidencePolicy.audienceFloor} non atteint`)
    ]),
    el("div", { className: "kw-two" }, [
      el("div", {}, [
        el("h3", { text: "Raisons de compilation" }),
        el("ul", {}, world.receipt.whyGenerated.map((item) => el("li", { text: item })))
      ]),
      el("div", {}, [
        el("h3", { text: "Autorité" }),
        el("ul", {}, [
          el("li", { text: `Publication automatique : ${world.receipt.authority.canPublish ? "OUI" : "NON"}` }),
          el("li", { text: `Mutation du statut de preuve : ${world.receipt.authority.canMutateEvidence ? "OUI" : "NON"}` }),
          el("li", { text: "Autorité humaine finale : OUI" })
        ])
      ])
    ])
  ]);
}

function renderObjects(world) {
  const cards = world.objects.map((object) => el("article", { className: "kw-object" }, [
    el("div", { className: "kw-object-head" }, [badge(object.evidenceLevel, "evidence"), el("code", { text: object.id })]),
    el("h3", { text: object.title }),
    el("small", { text: object.kind })
  ]));
  return el("section", { className: "kw-section" }, [
    el("div", { className: "kw-section-head" }, [
      el("div", {}, [el("p", { className: "eyebrow", text: "SHARED KNOWLEDGE KERNEL" }), el("h2", { text: "Même corpus, lentilles différentes" })]),
      badge(`${world.objects.length} objets`)
    ]),
    el("div", { className: "kw-object-grid" }, cards)
  ]);
}

function renderWorldDiff(general, selected) {
  const diff = worldDiff(general, selected);
  return el("section", { className: "kw-section" }, [
    el("div", { className: "kw-section-head" }, [
      el("div", {}, [el("p", { className: "eyebrow", text: "PERSONALIZATION DIFF" }), el("h2", { text: "Ce qui change — et ce qui ne change pas" })]),
      badge(diff.evidenceChanged ? "EVIDENCE CHANGED" : "EVIDENCE INVARIANT", diff.evidenceChanged ? "hold" : "pass")
    ]),
    el("div", { className: "kw-two" }, [
      el("div", {}, [
        el("h3", { text: "Ajouté par la lentille" }),
        el("div", { className: "kw-chip-row" }, diff.operatorsAdded.map((op) => el("code", { text: op }))),
        el("p", { className: "kw-fine", text: diff.operatorsAdded.length ? "Opérateurs adaptés à l'intention." : "Aucun opérateur supplémentaire." })
      ]),
      el("div", {}, [
        el("h3", { text: "Invariants" }),
        el("ul", {}, [
          el("li", { text: `Evidence canonique : ${selected.evidencePolicy.canonicalEvidenceLevel}` }),
          el("li", { text: "Le RelationshipState ne modifie pas la vérité." }),
          el("li", { text: "Les objets de connaissance conservent les mêmes identifiants." }),
          el("li", { text: "La publication automatique reste interdite." })
        ])
      ])
    ])
  ]);
}

function renderResiduals(world) {
  return el("section", { className: "kw-section kw-residual" }, [
    el("div", {}, [
      el("p", { className: "eyebrow", text: "RESIDUAL FIELD" }),
      el("h2", { text: "Le workspace révèle aussi ce qu'il manque" }),
      el("p", { text: "Une vue spécialisée ne doit pas seulement présenter le corpus : elle doit rendre le prochain travail vérifiable visible." })
    ]),
    el("ul", {}, world.residuals.map((item) => el("li", { text: item })))
  ]);
}

export function renderKnowledgeWorlds({ store, route }) {
  const receipt = knowledgeWorldKernelReceipt();
  const stats = store.statistics();
  const objects = sourceObjects(store);
  const residuals = [
    "Réplication indépendante de davantage de Hero Artifacts",
    "Bench utilisateur compréhension / source retrieval",
    "Prior-art decomposition sur les claims les plus ambitieux",
    "Rights/IP classification avant toute diffusion externe"
  ];
  const requestedProfile = String(route.query.get("profile") || "GENERAL").toUpperCase();
  const requestedMode = String(route.query.get("mode") || (requestedProfile === "RADIO_CANADA" ? "MEDIA" : requestedProfile === "RESEARCHER" ? "VERIFY" : "DISCOVER")).toUpperCase();
  const initialProfile = AUDIENCE_PROFILES[requestedProfile] ? requestedProfile : "GENERAL";
  const initialMode = WORLD_MODES[requestedMode] ? requestedMode : "DISCOVER";

  const root = el("div", { className: "kw-page" });
  const dynamic = el("div", { className: "kw-dynamic", "aria-live": "polite" });
  const profileSelect = el("select", { "aria-label": "Choisir une lentille d'audience" });
  const modeSelect = el("select", { "aria-label": "Choisir un mode cognitif" });

  for (const [id, profile] of Object.entries(AUDIENCE_PROFILES)) profileSelect.append(el("option", { value: id, text: `${id} — ${profile.label}`, selected: id === initialProfile }));
  for (const id of Object.keys(WORLD_MODES)) modeSelect.append(el("option", { value: id, text: id, selected: id === initialMode }));

  function build(profile, mode) {
    return compileWorld({
      entity: { id: profile === "RADIO_CANADA" ? "radio-canada" : "visitor", label: profile === "RADIO_CANADA" ? "Radio-Canada" : AUDIENCE_PROFILES[profile].label },
      profile,
      mode,
      evidenceLevel: "PROTOTYPE",
      objects,
      residuals,
      relationship: profile === "RADIO_CANADA" ? {
        role: "public-media",
        organization: "Radio-Canada",
        publicMandate: true,
        relationshipState: "DISCOVERED",
        declaredInterests: ["science", "culture", "public understanding"],
        permissions: []
      } : { relationshipState: "UNKNOWN", permissions: [] }
    });
  }

  const general = build("GENERAL", "DISCOVER");

  function paint() {
    const profile = profileSelect.value;
    const mode = modeSelect.value;
    const world = build(profile, mode);
    dynamic.replaceChildren(
      renderWorldCard(world),
      renderReceipt(world),
      renderWorldDiff(general, world),
      renderObjects(world),
      renderResiduals(world)
    );
  }

  profileSelect.addEventListener("change", paint);
  modeSelect.addEventListener("change", paint);

  root.append(
    el("section", { className: "kw-hero" }, [
      el("p", { className: "eyebrow", text: "Ω-PERSONALIZED-VERIFIED-KNOWLEDGE-WORLD-COMPILER-T" }),
      el("h1", { text: "Knowledge Worlds" }),
      el("p", { className: "kw-lede", text: "Une seule base de connaissances. Des interfaces spécialisées compilées par intention, audience et politique — sans personnaliser la vérité." }),
      el("code", { className: "kw-equation", text: "ENTITY/QUESTION → INTENT → KNOWLEDGE SUBGRAPH → OAK/PERMISSIONS → WORLD IR → INTERACTION PROGRAM → EVIDENCE → MEMORY" }),
      el("div", { className: "kw-grid-four" }, [
        stat("Profils", receipt.profiles, "Lentilles génératrices"),
        stat("Modes", receipt.modes, "Programmes cognitifs"),
        stat("ISA", receipt.operators, "Opérateurs réutilisables"),
        stat("Routes persistantes", receipt.persistentWorldRoutesRequired, "GO MIN")
      ])
    ]),
    el("section", { className: "kw-section" }, [
      el("div", { className: "kw-section-head" }, [
        el("div", {}, [el("p", { className: "eyebrow", text: "JIT WORKSPACE COMPILER" }), el("h2", { text: "Changer la lentille sans dupliquer le corpus" })]),
        badge("NO HIDDEN PSYCHOGRAPHICS", "pass")
      ]),
      el("div", { className: "kw-controls" }, [
        el("label", {}, [el("span", { text: "Lentille" }), profileSelect]),
        el("label", {}, [el("span", { text: "Mode" }), modeSelect])
      ]),
      el("p", { className: "kw-fine", text: `Corpus chargé : ${stats.theories} théories · ${stats.claims} claims · ${stats.relations} relations. Les trois dimensions restent dans le même Evidence Kernel.` })
    ]),
    dynamic,
    el("section", { className: "kw-section kw-two" }, [
      el("div", {}, [
        el("p", { className: "eyebrow", text: "COGNITIVE WEB ISA" }),
        el("h2", { text: "Pages = programmes d'interaction" }),
        el("div", { className: "kw-chip-row" }, COGNITIVE_WEB_ISA.map((op) => el("code", { text: op })))
      ]),
      el("div", {}, [
        el("p", { className: "eyebrow", text: "WORLD CONSTITUTION" }),
        el("h2", { text: "Personnaliser le chemin, jamais les faits" }),
        el("ul", {}, WORLD_CONSTITUTION.map((law) => el("li", { text: law })))
      ])
    ]),
    el("section", { className: "kw-section kw-boundary" }, [
      el("p", { className: "eyebrow", text: "OAK CLAIM BOUNDARY" }),
      el("h2", { text: "Compilateur de vues, pas moteur d'autorité" }),
      el("p", { text: "Cette surface est un prototype d'architecture et d'interface. Les profils décrivent des besoins de représentation déclarés ou génériques; ils ne sont pas des inférences psychographiques. Une relation, un média ou une institution ne peut jamais augmenter automatiquement le statut de preuve d'une théorie ni autoriser sa publication." })
    ])
  );
  paint();
  return root;
}
