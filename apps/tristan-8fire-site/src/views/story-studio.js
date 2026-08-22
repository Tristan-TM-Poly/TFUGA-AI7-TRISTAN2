"use strict";

import {
  STORY_CAPABILITIES,
  STORY_COMMANDS,
  STORY_CONSTITUTION,
  STORY_PIPELINE,
  automationValue,
  compileStoryProgram,
  evaluateSceneEnvelope,
  metaPromotionDecision,
  queryCapabilities,
  regenerationClosure
} from "../story-studio-kernel.js";

function el(tag, attrs = {}, children = []) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (key === "className") node.className = value;
    else if (key === "text") node.textContent = value;
    else if (key === "html") node.innerHTML = value;
    else if (key === "value") node.value = value;
    else if (key.startsWith("data-")) node.setAttribute(key, value);
    else if (key === "checked") node.checked = Boolean(value);
    else if (value !== undefined && value !== null) node.setAttribute(key, value);
  }
  for (const child of Array.isArray(children) ? children : [children]) if (child) node.append(child);
  return node;
}

const LAYERS = ["all", ...new Set(STORY_CAPABILITIES.map((item) => item.layer))];

function renderPipeline() {
  return el("section", { className: "story-section" }, [
    el("div", { className: "story-heading" }, [
      el("div", {}, [el("p", { className: "eyebrow", text: "Ω-STORYLIFE → Ω-OMNISTORY" }), el("h2", { text: "Un monde causal, plusieurs projections" })]),
      el("p", { text: "Le canon est un graphe vivant versionné; manga, anime, jeu, roman et web sont des compilations spécialisées." })
    ]),
    el("div", { className: "story-pipeline" }, STORY_PIPELINE.map((step, index) => el("div", {}, [
      el("span", { text: String(index + 1).padStart(2, "0") }),
      el("strong", { text: step })
    ])))
  ]);
}

function renderCompiler() {
  const intent = el("textarea", { id: "story-intent", rows: "4", placeholder: "Ex. Une cité orbitale fractale où la mémoire est une ressource politique…" });
  const medium = el("select", { id: "story-medium" }, ["manga", "anime", "game", "novel", "franchise"].map((name) => el("option", { value: name, text: name })));
  const genre = el("select", { id: "story-genre" }, ["hybrid", "science-fiction", "fantasy", "mystery", "romance", "action", "drama"].map((name) => el("option", { value: name, text: name })));
  const output = el("pre", { className: "story-output" }, [el("code", { text: "Aucun programme compilé." })]);
  const receipt = el("div", { className: "story-receipt" });

  const compileButton = el("button", { className: "story-button primary", type: "button", text: "Compiler StoryIR" });
  const attackButton = el("button", { className: "story-button", type: "button", text: "Attaquer le candidat" });
  const crystalButton = el("button", { className: "story-button", type: "button", text: "Tester la cristallisation" });

  let program = compileStoryProgram();
  const renderProgram = () => {
    program = compileStoryProgram({ intent: intent.value, medium: medium.value, genre: genre.value });
    output.firstChild.textContent = JSON.stringify({
      id: program.id,
      intent: program.intent,
      storyIR: program.storyIR,
      outputs: program.outputs,
      canonStatus: program.canonStatus,
      publication: program.publication
    }, null, 2);
    receipt.replaceChildren(
      el("span", { className: "story-pill hold", text: "DRAFT · HOLD" }),
      el("p", { text: "Generated != Canon. La compilation crée un candidat, jamais une promotion automatique." })
    );
  };

  compileButton.addEventListener("click", renderProgram);
  attackButton.addEventListener("click", () => {
    const gate = evaluateSceneEnvelope({ continuity: 0.82, causality: 0.76, rightsCleared: true, provenance: true, independentReview: false, attemptsCanon: true, verified: false });
    receipt.replaceChildren(
      el("span", { className: `story-pill ${gate.status === "PASS" ? "pass" : "hold"}`, text: `OAK ${gate.status}` }),
      el("p", { text: gate.blockers.length ? `Bloqueurs: ${gate.blockers.join(", ")}.` : "Aucun bloqueur détecté." })
    );
  });
  crystalButton.addEventListener("click", () => {
    const promotion = metaPromotionDecision({ verifiedGain: 0.31, complexity: 0.12, cost: 0.08, risk: 0.05, frozenBenchmark: true, independentJudge: true });
    const closure = regenerationClosure(["generate", "verify", "canon", "regenerate"], ["generate", "verify", "regenerate"]);
    const auto = automationValue({ futureWorkEliminated: 8, reliability: 0.85, implementationCost: 2, risk: 0.5 });
    receipt.replaceChildren(
      el("span", { className: `story-pill ${promotion.decision === "PROMOTE" ? "pass" : "hold"}`, text: promotion.decision }),
      el("p", { text: `Gain/burden=${promotion.ratio.toFixed(2)} · regeneration closure=${Math.round(closure.ratio * 100)}% · automation value=${auto.toFixed(2)}.` }),
      el("small", { text: closure.missing.length ? `Capacité manquante: ${closure.missing.join(", ")}.` : "Régénération complète." })
    );
  });

  return el("section", { className: "story-section story-compiler" }, [
    el("div", { className: "story-heading" }, [
      el("div", {}, [el("p", { className: "eyebrow", text: "STORY COMPILER" }), el("h2", { text: "Intention → StoryIR → preuves" })]),
      el("p", { text: "Le sandbox ci-dessous matérialise la logique du studio sans publier ni canoniser automatiquement." })
    ]),
    el("div", { className: "story-compiler-grid" }, [
      el("div", { className: "story-control" }, [
        el("label", {}, [el("span", { text: "Intention" }), intent]),
        el("div", { className: "story-inline" }, [el("label", {}, [el("span", { text: "Média" }), medium]), el("label", {}, [el("span", { text: "Genre" }), genre])]),
        el("div", { className: "story-actions" }, [compileButton, attackButton, crystalButton]),
        receipt
      ]),
      output
    ])
  ]);
}

function capabilityCard(item) {
  return el("article", { className: "story-capability", "data-layer": item.layer }, [
    el("div", { className: "story-cap-top" }, [
      el("code", { text: item.id }),
      el("span", { className: `story-pill ${item.status === "core" ? "core" : "experimental"}`, text: item.status })
    ]),
    el("h3", { text: item.title }),
    el("p", { text: item.purpose }),
    el("small", { text: item.layer })
  ]);
}

function renderCapabilities() {
  const grid = el("div", { className: "story-cap-grid" });
  const count = el("strong", { className: "story-count" });
  const search = el("input", { type: "search", placeholder: "Filtrer : canon, dialogue, meta, OAK, animation…", "aria-label": "Filtrer les capacités Storyworld Studio" });
  let activeLayer = "all";

  const refresh = () => {
    const items = queryCapabilities(search.value, activeLayer);
    count.textContent = `${items.length} / ${STORY_CAPABILITIES.length} capacités`;
    grid.replaceChildren(...items.map(capabilityCard));
  };

  search.addEventListener("input", refresh);
  const filters = el("div", { className: "story-layer-filters" }, LAYERS.map((layer) => {
    const button = el("button", { type: "button", className: layer === "all" ? "is-active" : "", text: layer });
    button.addEventListener("click", () => {
      activeLayer = layer;
      for (const sibling of button.parentElement.children) sibling.classList.toggle("is-active", sibling === button);
      refresh();
    });
    return button;
  }));
  refresh();

  return el("section", { className: "story-section" }, [
    el("div", { className: "story-heading" }, [
      el("div", {}, [el("p", { className: "eyebrow", text: "CAPABILITY FOREST" }), el("h2", { text: "Tout le système branché comme registre vivant" })]),
      el("p", { text: "Core = invariant/primitive d'architecture. Experimental = hypothèse computationnelle à tester; le label n'est pas une preuve scientifique." })
    ]),
    el("div", { className: "story-filterbar" }, [search, count]),
    filters,
    grid
  ]);
}

function renderCommands() {
  const terminal = el("code", { className: "story-command-selected", text: "GO STORY META MAX" });
  const buttons = STORY_COMMANDS.map((command) => {
    const button = el("button", { className: "story-command", type: "button", text: command });
    button.addEventListener("click", () => { terminal.textContent = command; });
    return button;
  });
  return el("section", { className: "story-section story-two" }, [
    el("div", {}, [
      el("p", { className: "eyebrow", text: "COMMAND DSL" }),
      el("h2", { text: "Une surface simple au-dessus d'un studio complexe" }),
      el("p", { text: "Les commandes sont des intentions de workflow. Elles ne donnent ni autorité de publication, ni droit de cloner une identité artistique ou vocale." }),
      terminal
    ]),
    el("div", { className: "story-command-grid" }, buttons)
  ]);
}

function renderConstitution() {
  return el("section", { className: "story-section story-boundary" }, [
    el("div", { className: "story-heading" }, [
      el("div", {}, [el("p", { className: "eyebrow", text: "OAK / RIGHTS / CANON" }), el("h2", { text: "Constitution du studio" })]),
      el("span", { className: "story-pill hold", text: "PROTOTYPE · HUMAN-GATED" })
    ]),
    el("div", { className: "story-law-grid" }, STORY_CONSTITUTION.map((law) => el("code", { text: law }))),
    el("p", { className: "story-fineprint", text: "VisualDNA décrit des primitives abstraites originales; VoiceGenome suppose voix originales ou droits explicites. Audience Mirrors restent des sondes logicielles. Les métriques narratives sont des instruments de contrôle expérimental, pas des lois universelles de l'art." })
  ]);
}

export function renderStoryStudio() {
  return el("div", { className: "story-page" }, [
    el("section", { className: "story-hero" }, [
      el("p", { className: "eyebrow", text: "Ω-MANGA-ANIME-MAX → Ω-META-STORYGENESIS → Ω-OMNISTORY" }),
      el("h1", { text: "Storyworld Studio" }),
      el("p", { className: "story-lede", text: "Un studio génératif borné qui construit des univers causaux exécutables, les projette vers manga/anime/jeu/roman, falsifie ses propres sorties, cristallise peu et régénère depuis BOOK0_MIN." }),
      el("code", { className: "story-equation", text: "GENERATE → ATTACK → MEASURE → IMPROVE → ABLATE → COMPRESS → CRYSTALLIZE → REGENERATE" }),
      el("div", { className: "story-hero-metrics" }, [
        el("div", {}, [el("strong", { text: String(STORY_CAPABILITIES.length) }), el("span", { text: "capacités branchées" })]),
        el("div", {}, [el("strong", { text: String(STORY_COMMANDS.length) }), el("span", { text: "commandes DSL" })]),
        el("div", {}, [el("strong", { text: "R0.1" }), el("span", { text: "prototype interactif" })])
      ])
    ]),
    renderPipeline(),
    renderCompiler(),
    renderCapabilities(),
    renderCommands(),
    renderConstitution()
  ]);
}
