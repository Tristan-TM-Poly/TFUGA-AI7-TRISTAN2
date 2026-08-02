"use strict";

import { badge, element, emptyState, link, sectionHeader } from "../ui.js";
import { exportGraphml } from "../exporters.js";

const SVG_NS = "http://www.w3.org/2000/svg";

function svg(tag, attributes = {}) {
  const node = document.createElementNS(SVG_NS, tag);
  for (const [key, value] of Object.entries(attributes)) node.setAttribute(key, String(value));
  return node;
}

function deterministicLayout(theories, width, height) {
  const families = new Map();
  for (const theory of theories) {
    const bucket = families.get(theory.family) || [];
    bucket.push(theory);
    families.set(theory.family, bucket);
  }
  const familyEntries = [...families.entries()].sort(([a], [b]) => a.localeCompare(b));
  const centerX = width / 2;
  const centerY = height / 2;
  const outerRadius = Math.min(width, height) * 0.34;
  const positions = new Map();
  familyEntries.forEach(([family, items], familyIndex) => {
    const familyAngle = (Math.PI * 2 * familyIndex) / familyEntries.length - Math.PI / 2;
    const familyX = centerX + Math.cos(familyAngle) * outerRadius;
    const familyY = centerY + Math.sin(familyAngle) * outerRadius;
    const localRadius = Math.min(96, 22 + items.length * 7);
    items.sort((a, b) => a.ordinal - b.ordinal).forEach((item, index) => {
      const localAngle = (Math.PI * 2 * index) / Math.max(1, items.length);
      positions.set(item.id, {
        x: familyX + Math.cos(localAngle) * localRadius,
        y: familyY + Math.sin(localAngle) * localRadius,
        family
      });
    });
  });
  return positions;
}

function relationSubset(store, focus, depth) {
  if (!focus) return { theories: store.theories, relations: store.relations };
  const seen = new Set([focus]);
  let frontier = new Set([focus]);
  for (let level = 0; level < depth; level += 1) {
    const next = new Set();
    for (const id of frontier) {
      for (const relation of [...store.getOutgoing(id), ...store.getIncoming(id)]) {
        const other = relation.source === id ? relation.target : relation.source;
        if (!seen.has(other)) { seen.add(other); next.add(other); }
      }
    }
    frontier = next;
  }
  return {
    theories: [...seen].map((id) => store.getTheory(id)).filter(Boolean),
    relations: store.relations.filter((relation) => seen.has(relation.source) && seen.has(relation.target))
  };
}

function drawGraph(container, store, subset, focus) {
  const width = 1100;
  const height = 720;
  const positions = deterministicLayout(subset.theories, width, height);
  const graphic = svg("svg", { viewBox: `0 0 ${width} ${height}`, role: "img", "aria-label": "Graphe de navigation des théories" });
  const defs = svg("defs");
  const marker = svg("marker", { id: "arrow", viewBox: "0 0 10 10", refX: "8", refY: "5", markerWidth: "5", markerHeight: "5", orient: "auto-start-reverse" });
  marker.append(svg("path", { d: "M 0 0 L 10 5 L 0 10 z", class: "graph-arrow" }));
  defs.append(marker);
  graphic.append(defs);

  const edges = svg("g", { class: "graph-edges" });
  for (const relation of subset.relations) {
    const source = positions.get(relation.source);
    const target = positions.get(relation.target);
    if (!source || !target) continue;
    const line = svg("line", {
      x1: source.x, y1: source.y, x2: target.x, y2: target.y,
      class: `graph-edge kind-${relation.kind.replaceAll("_", "-")}`,
      "data-id": relation.id,
      "data-kind": relation.kind,
      "stroke-opacity": Math.max(0.2, Number(relation.strength || 0.5)),
      "marker-end": "url(#arrow)"
    });
    const title = svg("title");
    title.textContent = `${relation.kind}: ${relation.rationale}`;
    line.append(title);
    edges.append(line);
  }
  graphic.append(edges);

  const nodes = svg("g", { class: "graph-nodes" });
  for (const theory of subset.theories) {
    const position = positions.get(theory.id);
    if (!position) continue;
    const group = svg("g", { class: `graph-node${theory.id === focus ? " is-focus" : ""}`, transform: `translate(${position.x},${position.y})`, tabindex: "0", role: "link", "aria-label": `${theory.symbol}, ${theory.title}` });
    group.append(svg("circle", { r: theory.id === focus ? 14 : 9, class: `node-${theory.maturity}` }));
    const label = svg("text", { x: "13", y: "4" });
    label.textContent = theory.symbol;
    const title = svg("title");
    title.textContent = `${theory.title}\n${theory.maturity} · ${theory.evidence}`;
    group.append(label, title);
    const open = () => { window.location.hash = `#/theory/${encodeURIComponent(theory.id)}`; };
    group.addEventListener("click", open);
    group.addEventListener("keydown", (event) => { if (event.key === "Enter" || event.key === " ") open(); });
    nodes.append(group);
  }
  graphic.append(nodes);
  container.replaceChildren(graphic);
}

export function renderGraph({ store, route }) {
  const focus = route.params.focus || route.query.get("focus") || "";
  const depth = Math.max(1, Math.min(3, Number(route.query.get("depth") || 1)));
  if (focus && !store.getTheory(focus)) return emptyState("Nœud introuvable", "La théorie demandée n’existe pas dans le graphe public.");
  const subset = relationSubset(store, focus, depth);
  const root = element("div", { className: "view graph-view" });
  root.append(sectionHeader("Hypergraphe public", focus ? `Voisinage de ${store.getTheory(focus).symbol}` : "44 nœuds, 268 relations de navigation", "La géométrie et la force des liens servent à explorer le corpus. Elles ne constituent pas une preuve de causalité, d’identité ou de supériorité."));

  const controls = element("form", { className: "graph-controls" }, [
    element("label", {}, [element("span", { text: "Nœud focal" }), element("select", { name: "focus" }, [
      element("option", { value: "", text: "Graphe complet", selected: !focus }),
      ...store.theories.slice().sort((a, b) => a.title.localeCompare(b.title, "fr")).map((theory) => element("option", { value: theory.id, text: `${theory.symbol} — ${theory.title}`, selected: theory.id === focus }))
    ])]),
    element("label", {}, [element("span", { text: "Profondeur" }), element("select", { name: "depth" }, [1, 2, 3].map((value) => element("option", { value, text: `${value} saut${value > 1 ? "s" : ""}`, selected: value === depth })))]),
    element("button", { type: "submit", className: "button primary", text: "Afficher" }),
    link("Réinitialiser", "#/graph", "button secondary"),
    element("button", { type: "button", className: "button secondary", text: "Exporter GraphML", onclick: () => exportGraphml(subset.theories, subset.relations) })
  ]);
  controls.addEventListener("submit", (event) => {
    event.preventDefault();
    const data = new FormData(controls);
    const selected = String(data.get("focus") || "");
    const selectedDepth = String(data.get("depth") || 1);
    window.location.hash = selected ? `#/graph/${encodeURIComponent(selected)}?depth=${selectedDepth}` : "#/graph";
  });
  root.append(controls);
  root.append(element("div", { className: "graph-legend" }, [
    badge(`${subset.theories.length} nœuds`, "neutral"),
    badge(`${subset.relations.length} relations`, "neutral"),
    badge("prototype", "success"), badge("architecture", "warning"), badge("hypothèse", "danger")
  ]));
  const canvas = element("div", { className: "graph-canvas" });
  root.append(canvas);
  queueMicrotask(() => drawGraph(canvas, store, subset, focus));
  return root;
}
