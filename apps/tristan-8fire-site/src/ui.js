"use strict";

export function element(tag, options = {}, children = []) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(options)) {
    if (value === undefined || value === null) continue;
    if (key === "className") node.className = value;
    else if (key === "text") node.textContent = String(value);
    else if (key === "html") throw new Error("Unsafe html option is forbidden");
    else if (key === "dataset") Object.assign(node.dataset, value);
    else if (key.startsWith("on") && typeof value === "function") node.addEventListener(key.slice(2).toLowerCase(), value);
    else if (key in node && !key.startsWith("aria")) node[key] = value;
    else node.setAttribute(key, String(value));
  }
  for (const child of Array.isArray(children) ? children : [children]) {
    if (child === undefined || child === null || child === false) continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return node;
}

export function fragment(...children) {
  const value = document.createDocumentFragment();
  for (const child of children.flat(Infinity)) if (child !== undefined && child !== null) value.append(child instanceof Node ? child : document.createTextNode(String(child)));
  return value;
}

export function link(label, href, className = "") {
  return element("a", { text: label, href, className });
}

export function badge(label, tone = "neutral") {
  return element("span", { text: label, className: `pill pill-${tone}` });
}

export function metric(label, value, note = "") {
  return element("article", { className: "metric-card" }, [
    element("strong", { text: value }),
    element("span", { text: label }),
    note ? element("small", { text: note }) : null
  ]);
}

export function emptyState(title, detail) {
  return element("section", { className: "empty-state" }, [
    element("h2", { text: title }),
    element("p", { text: detail })
  ]);
}

export function sectionHeader(eyebrow, title, description = "") {
  return element("header", { className: "view-heading" }, [
    element("div", {}, [element("p", { className: "eyebrow", text: eyebrow }), element("h1", { text: title })]),
    description ? element("p", { className: "view-description", text: description }) : null
  ]);
}

const OAK_LABELS = Object.freeze({
  verite: "Vérité",
  utilite: "Utilité",
  testabilite: "Testabilité",
  simplicite: "Simplicité",
  valeur: "Valeur",
  protection: "Protection"
});

export function oakBars(oak = {}) {
  const container = element("div", { className: "oak-profile" });
  for (const [key, label] of Object.entries(OAK_LABELS)) {
    const value = Math.max(0, Math.min(1, Number(oak[key] || 0)));
    container.append(element("div", { className: "oak-line" }, [
      element("span", { text: label }),
      element("span", { className: "oak-track", "aria-hidden": "true" }, [
        element("i", { style: `width:${Math.round(value * 100)}%` })
      ]),
      element("output", { text: value.toFixed(2), "aria-label": `${label} ${Math.round(value * 100)} pour cent` })
    ]));
  }
  return container;
}

export function publicationGate(publication = {}) {
  const gates = [
    ["OAK", publication.oak_gate],
    ["IP", publication.ip_gate],
    ["Vie privée", publication.privacy_gate],
    ["Sécurité", publication.security_gate]
  ];
  return element("div", { className: "gate-row", "aria-label": "État des quatre portes de publication" }, gates.map(([label, passed]) =>
    badge(`${passed ? "✓" : "×"} ${label}`, passed ? "success" : "danger")
  ));
}

export function list(items, renderer, className = "stack") {
  const container = element("div", { className });
  for (const item of items) container.append(renderer(item));
  return container;
}

export function table(headers, rows, caption = "") {
  const head = element("thead", {}, [element("tr", {}, headers.map((header) => element("th", { text: header, scope: "col" })))]);
  const body = element("tbody");
  for (const row of rows) body.append(element("tr", {}, row.map((cell) => element("td", {}, [cell instanceof Node ? cell : String(cell ?? "")]))));
  return element("div", { className: "table-scroll" }, [
    element("table", {}, [caption ? element("caption", { text: caption }) : null, head, body])
  ]);
}

export function announce(message) {
  const live = document.querySelector("#live-region");
  if (!live) return;
  live.textContent = "";
  window.setTimeout(() => { live.textContent = message; }, 20);
}

export function formatPercent(value) {
  return new Intl.NumberFormat("fr-CA", { style: "percent", maximumFractionDigits: 0 }).format(Number(value || 0));
}

export function formatNumber(value) {
  return new Intl.NumberFormat("fr-CA").format(Number(value || 0));
}
