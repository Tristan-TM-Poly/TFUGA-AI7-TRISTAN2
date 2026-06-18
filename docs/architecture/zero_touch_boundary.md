# Zero-Touch Boundary

Status: OAK-3 operational safety seed.  
Related issue: #32.

Zero-touch means reducing manual friction. It does not mean removing review, evidence or responsibility.

---

## 1. Allowed zero-touch actions

Agents and automation may prepare:

- branches;
- draft pull requests;
- issues;
- documentation drafts;
- code patches;
- tests;
- benchmark scripts;
- OAK reports;
- residue lists;
- review checklists;
- reproducible artifacts.

---

## 2. Actions requiring explicit review

These actions require a human decision or a clear project policy:

- marking a major claim as canon;
- merging a pull request;
- submitting a publication;
- sending external messages;
- spending money;
- deleting review history;
- deleting negative memory;
- claiming measured status without data records.

---

## 3. Required output for agentic work

Every automated or semi-automated action must produce:

```text
trace + evidence + residue + status + next_action
```

If a task cannot produce those fields, it remains draft work.

---

## 4. Status gates

```text
NARRATIVE -> CONCEPT -> FORMALIZED -> SIMULATION_READY -> SIMULATED -> MEASUREMENT_READY -> MEASURED -> REPLICATED -> CERTIFIED
```

A transition requires review material. The stronger the status, the stronger the required evidence.

---

## 5. Practical rule

Zero-touch may accelerate construction, but not certification.

```text
automation builds; OAK reviews; canon remembers.
```
