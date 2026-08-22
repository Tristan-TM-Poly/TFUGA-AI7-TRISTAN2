"use strict";

import { announce, badge, element, metric, sectionHeader, table } from "../ui.js";
import {
  QUEBEC_GROUP_FAMILIES,
  marketplaceCapabilityStatus,
  proofValueReceipt,
  uploadGate
} from "../marketplace-kernel.js";

function money(value) {
  return new Intl.NumberFormat("fr-CA", { style: "currency", currency: "CAD" }).format(Number(value || 0));
}

function configuredCapabilities() {
  const raw = globalThis.TRISTAN_MARKETPLACE_CAPABILITIES || {};
  return marketplaceCapabilityStatus({
    identity: raw.identity,
    privateStorage: raw.privateStorage,
    malwareScanning: raw.malwareScanning,
    payments: raw.payments,
    entitlementLedger: raw.entitlementLedger,
    taxConfig: raw.taxConfig
  });
}

function statusPanel() {
  const status = configuredCapabilities();
  const rows = Object.entries(status.requirements).map(([key, ready]) => [
    key,
    badge(ready ? "Prêt" : "À configurer", ready ? "success" : "warning")
  ]);
  return element("section", { className: "market-card" }, [
    element("div", { className: "market-card-heading" }, [
      element("div", {}, [element("p", { className: "eyebrow", text: "Production gate" }), element("h2", { text: "État du coffre payant" })]),
      badge(status.status, status.ready ? "success" : "warning")
    ]),
    element("p", { text: status.ready
      ? "Les capacités critiques sont déclarées prêtes. Les opérations restent vérifiées côté serveur."
      : "Fail-closed : aucun upload privé, paiement ni téléchargement réel n'est exécuté tant que toutes les capacités critiques ne sont pas configurées." }),
    table(["Capacité", "État"], rows, "Gates de production")
  ]);
}

function uploadWorkbench() {
  const fileInput = element("input", { type: "file", multiple: true, id: "market-upload-files" });
  const rights = element("input", { type: "checkbox", id: "market-rights" });
  const privacy = element("input", { type: "checkbox", id: "market-privacy" });
  const subscriber = element("input", { type: "checkbox", id: "market-subscriber", checked: true });
  const output = element("div", { className: "market-results", "aria-live": "polite" });
  const inspectButton = element("button", { type: "button", className: "button primary", text: "Analyser avant upload" });
  const uploadButton = element("button", { type: "button", className: "button", text: "Envoyer au coffre privé" });

  inspectButton.addEventListener("click", () => {
    const files = [...(fileInput.files || [])];
    output.replaceChildren();
    if (!files.length) {
      output.append(element("p", { className: "notice", text: "Sélectionne au moins un document ou une archive." }));
      return;
    }
    const rows = files.map((file) => {
      const gate = uploadGate(file, {
        isSubscriber: subscriber.checked,
        rightsDeclared: rights.checked,
        privacyDeclared: privacy.checked,
        containsPersonalData: false,
        privacyImpactAssessment: false
      });
      return [
        file.name,
        `${(file.size / 1024 / 1024).toFixed(2)} Mo`,
        gate.classification.category,
        badge(gate.classification.risk, gate.classification.risk === "ALLOW" ? "success" : gate.classification.risk === "BLOCK" ? "danger" : "warning"),
        badge(gate.status, gate.status === "READY_FOR_PRIVATE_UPLOAD" ? "success" : gate.status === "HOLD" ? "danger" : "warning")
      ];
    });
    output.append(table(["Fichier", "Taille", "Classe", "Risque", "Gate"], rows, "Analyse locale des fichiers"));
    announce(`${files.length} fichier(s) analysé(s).`);
  });

  uploadButton.addEventListener("click", () => {
    const status = configuredCapabilities();
    if (!status.ready) {
      output.prepend(element("p", { className: "notice warning", text: "Upload réel refusé : backend sécurisé non configuré. L'analyse locale demeure disponible." }));
      announce("Upload réel refusé par le gate de production.");
      return;
    }
    output.prepend(element("p", { className: "notice", text: "Le backend est déclaré prêt, mais cette vue statique doit être reliée à l'adaptateur d'API de production avant l'envoi." }));
  });

  return element("section", { className: "market-card" }, [
    element("div", { className: "market-card-heading" }, [
      element("div", {}, [element("p", { className: "eyebrow", text: "Subscriber vault" }), element("h2", { text: "Upload documents, ZIP, données et code" })]),
      badge("Private-by-default", "success")
    ]),
    element("p", { text: "Les fichiers sont classés avant envoi. Les archives et contenus actifs vont en quarantaine; le code peut être stocké comme texte mais n'est jamais exécuté automatiquement." }),
    element("div", { className: "market-form-grid" }, [
      element("label", { className: "market-field" }, [element("span", { text: "Fichiers" }), fileInput]),
      element("label", { className: "market-check" }, [subscriber, element("span", { text: "Compte abonné authentifié" })]),
      element("label", { className: "market-check" }, [rights, element("span", { text: "Je déclare détenir les droits nécessaires" })]),
      element("label", { className: "market-check" }, [privacy, element("span", { text: "Je confirme avoir vérifié la vie privée et les renseignements personnels" })])
    ]),
    element("div", { className: "market-actions" }, [inspectButton, uploadButton]),
    output
  ]);
}

function valueWorkbench() {
  const evidence = element("select", { id: "value-evidence" }, [
    ...["HYPOTHESIS", "DOCUMENTED", "PROTOTYPE", "MEASURED", "REPLICATED", "INDEPENDENTLY_VERIFIED", "CONTRACTUALLY_VALIDATED"].map((value) => element("option", { value, text: value }))
  ]);
  evidence.value = "MEASURED";
  const independent = element("input", { type: "number", min: 0, max: 20, value: 1, step: 1 });
  const utility = element("input", { type: "range", min: 0, max: 1, step: 0.05, value: 0.8 });
  const reproducibility = element("input", { type: "range", min: 0, max: 1, step: 0.05, value: 0.75 });
  const provenance = element("input", { type: "range", min: 0, max: 1, step: 0.05, value: 1 });
  const rights = element("input", { type: "range", min: 0, max: 1, step: 0.05, value: 1 });
  const uniqueness = element("input", { type: "range", min: 0, max: 1, step: 0.05, value: 0.6 });
  const buyerValidation = element("input", { type: "range", min: 0, max: 1, step: 0.05, value: 0.5 });
  const output = element("div", { className: "market-value-output" });
  const button = element("button", { type: "button", className: "button primary", text: "Calculer le Value Receipt" });

  const renderReceipt = () => {
    const receipt = proofValueReceipt({
      evidenceLevel: evidence.value,
      independentReceipts: independent.value,
      utility: utility.value,
      reproducibility: reproducibility.value,
      provenance: provenance.value,
      rights: rights.value,
      uniqueness: uniqueness.value,
      freshness: 0.8,
      buyerValidation: buyerValidation.value
    });
    output.replaceChildren(
      metric("Score de valeur", receipt.score.toFixed(2), receipt.status),
      metric("Prix suggéré", money(receipt.suggestedCad), "CAD · calcul serveur à reproduire"),
      metric("Fourchette OAK", `${money(receipt.floorCad)} – ${money(receipt.ceilingCad)}`, "prix hors zone = HOLD"),
      element("p", { className: "notice", text: "Le prix est une décision commerciale bornée par les preuves, pas une mesure objective de vérité ni de valeur humaine." })
    );
  };
  button.addEventListener("click", renderReceipt);
  renderReceipt();

  const rangeField = (label, input) => element("label", { className: "market-field" }, [element("span", { text: label }), input]);
  return element("section", { className: "market-card" }, [
    element("div", { className: "market-card-heading" }, [
      element("div", {}, [element("p", { className: "eyebrow", text: "Proof-carrying pricing" }), element("h2", { text: "Prix selon valeur prouvée" })]),
      badge("CAD", "neutral")
    ]),
    element("p", { text: "La valeur de téléchargement est calculée à partir de la preuve, de l'utilité, de la reproductibilité, de la provenance, des droits et de validations indépendantes. Le client ne peut jamais fixer le prix payé côté serveur." }),
    element("div", { className: "market-form-grid compact" }, [
      element("label", { className: "market-field" }, [element("span", { text: "Niveau de preuve" }), evidence]),
      element("label", { className: "market-field" }, [element("span", { text: "Receipts indépendants" }), independent]),
      rangeField("Utilité observée", utility),
      rangeField("Reproductibilité", reproducibility),
      rangeField("Provenance", provenance),
      rangeField("Droits", rights),
      rangeField("Unicité", uniqueness),
      rangeField("Validation acheteurs", buyerValidation)
    ]),
    button,
    output
  ]);
}

function groupTwinRegistry() {
  const rows = QUEBEC_GROUP_FAMILIES.map((family) => [
    family.label,
    family.mode,
    family.examples,
    family.id === "indigenous" ? badge("gouvernance + consentement", "warning") : badge("collectif seulement", "success")
  ]);
  return element("section", { className: "market-card span-2" }, [
    element("div", { className: "market-card-heading" }, [
      element("div", {}, [element("p", { className: "eyebrow", text: "Québec Twin Registry" }), element("h2", { text: "Jumeaux des différents groupes du Québec" })]),
      badge(`${QUEBEC_GROUP_FAMILIES.length} familles`, "neutral")
    ]),
    element("p", { text: "Le registre est génératif : chaque organisation ou collectif admissible devient un jumeau avec sources, observables, incertitude, date de vérification et OAK gates. Il ne prétend pas énumérer littéralement tous les groupes existants du Québec." }),
    element("ul", { className: "market-guardrails" }, [
      element("li", { text: "Aucun profil individuel ni inférence d'appartenance à un groupe." }),
      element("li", { text: "Aucune inférence de caractéristiques sensibles à partir d'un jumeau collectif." }),
      element("li", { text: "Données publiques, agrégées ou explicitement consenties; seuils anti-réidentification." }),
      element("li", { text: "Pour les communautés exigeant une gouvernance propre des données, le consentement et l'autorité de gouvernance sont un gate dur." })
    ]),
    table(["Famille", "Mode de données", "Exemples", "Protection"], rows, "Familles de jumeaux collectifs du Québec")
  ]);
}

function paidDownloadArchitecture() {
  const steps = [
    ["1", "Upload privé", "Ticket signé + stockage objet privé; jamais de bucket public."],
    ["2", "Quarantaine", "Scan malware, archive bomb, macros et contenu actif; aucune exécution."],
    ["3", "Value Receipt", "Prix recalculé côté serveur à partir d'evidence receipts versionnés."],
    ["4", "Checkout", "Stripe Checkout; taxes configurées selon le statut fiscal réel."],
    ["5", "Entitlement", "Ledger serveur liant achat, utilisateur, asset, prix, taxes et statut."],
    ["6", "Download", "URL courte durée ou streaming privé après revalidation; journal de preuve."],
    ["7", "Révocation", "Remboursement, retrait de droits, malware ou problème de confidentialité coupe l'accès futur."],
    ["8", "Twin ingest", "Seules les données autorisées et suffisamment agrégées alimentent un jumeau de groupe."]
  ];
  return element("section", { className: "market-card span-2" }, [
    element("div", { className: "market-card-heading" }, [
      element("div", {}, [element("p", { className: "eyebrow", text: "Zero-trust flow" }), element("h2", { text: "Pipeline payant de bout en bout" })]),
      badge("server-authoritative", "success")
    ]),
    table(["Étape", "Composant", "Invariant"], steps, "Pipeline upload → paiement → download → twin")
  ]);
}

export function renderMarketplace() {
  return element("section", { className: "view market-view" }, [
    sectionHeader("Ω-VALUE-MARKETPLACE × QC-TWIN", "Coffre, téléchargements payants et jumeaux du Québec", "Transformer les uploads des abonnés en actifs privés, vérifiés et téléchargeables selon une valeur prouvée, tout en maintenant des jumeaux collectifs gouvernés par provenance, consentement et OAK."),
    element("div", { className: "market-grid" }, [
      statusPanel(),
      valueWorkbench(),
      uploadWorkbench(),
      groupTwinRegistry(),
      paidDownloadArchitecture()
    ])
  ]);
}
