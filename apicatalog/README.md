# Integration COE — API Catalog

A lightweight, standalone API catalog and migration planning tool for the MuleSoft 4.3 → 4.9 migration programme. No backend, no database, no build step — four HTML files and one JSON file that work together from a folder or any static file server.

---

## Contents

- [Project Overview](#project-overview)
- [File Structure](#file-structure)
- [How to Run](#how-to-run)
- [Pages & Features](#pages--features)
  - [index.html — Catalog Viewer](#indexhtml--catalog-viewer)
  - [editor.html — Catalog Editor](#editorhtml--catalog-editor)
  - [dependencies.html — Dependency Visualiser](#dependencieshtml--dependency-visualiser)
- [Data Schema](#data-schema)
  - [Top-level fields](#top-level-fields)
  - [API entry fields](#api-entry-fields)
  - [Security COE block](#security-coe-block)
  - [Solution Design COE block](#solution-design-coe-block)
  - [Operations COE block](#operations-coe-block)
  - [Consumer / Upstream entry](#consumer--upstream-entry)
- [Workflow — Updating the Catalog](#workflow--updating-the-catalog)
- [Populating from Real Data](#populating-from-real-data)
- [Tribe & Spotify Model Mapping](#tribe--spotify-model-mapping)
- [Migration Status Values](#migration-status-values)
- [Theme](#theme)
- [Extending the Catalog](#extending-the-catalog)
  - [Adding a new Group By dimension](#adding-a-new-group-by-dimension)
  - [Adding a new API layer type](#adding-a-new-api-layer-type)
  - [Adding a new CoE metadata section](#adding-a-new-coe-metadata-section)
- [Known Constraints](#known-constraints)
- [Roadmap / Future Considerations](#roadmap--future-considerations)

---

## Project Overview

This toolset was built to support the Integration COE lead during the MuleSoft 4.3 → 4.9 migration RFP and landscape assessment. It serves four distinct audiences:

| Persona | Primary tool | Primary question answered |
|---|---|---|
| **COE Lead / Architect** | All pages | What is our full API landscape and migration posture? |
| **Head of Tribe** | `dependencies.html` → Icicle | What APIs does my tribe own and what is our readiness? |
| **Solution Design COE** | `index.html` → drawer → Solution Design tab | What patterns, SLAs and ADRs are documented? |
| **Security COE** | `index.html` → drawer → Security tab | What auth, compliance flags and vulnerabilities exist? |
| **Operations COE** | `index.html` → drawer → Operations tab | Who do I call, where is the runbook, what are the fragilities? |
| **Migration planner** | `dependencies.html` → Dependency Graph | What must migrate before what? Who is at regression risk? |

The catalog is **Git-controlled**. `api-data.json` is the single source of truth. All pages are read-only viewers except `editor.html`, which exports a new `api-data.json` for Git commit.

---

## File Structure

```
/
├── api-data.json          ← Single source of truth — commit this to Git
├── index.html             ← Multi-view catalog viewer (all personas)
├── editor.html            ← Form-driven catalog editor
├── dependencies.html      ← D3.js visualisation — tribe icicle + dependency graph
└── README.md              ← This file
```

All four HTML files are self-contained — no `node_modules`, no build step, no external dependencies beyond Google Fonts and D3.js (both loaded from CDN).

---

## How to Run

### Option A — Local static server (recommended)

This is the correct way to run the tool. It ensures `api-data.json` is auto-loaded on every page open with no manual intervention.

**Python (built into macOS and most Linux):**
```bash
cd /path/to/catalog-folder
python3 -m http.server 8080
```
Then open: `http://localhost:8080/index.html`

**Node.js:**
```bash
npx serve .
```

Leave the terminal window open while using the tool. All pages will auto-load `api-data.json` on open.

### Option B — Open files directly (file://)

Open `index.html` directly in a browser. Because browsers block local `fetch()` calls under the `file://` protocol, `api-data.json` will **not** auto-load. Use the **📂 Load JSON** button in the header to manually load `api-data.json` each session.

> **This is intentional** — it enforces that squad members always load from the committed version rather than working off a stale local copy. The manual load step = the Git pull.

### GitHub Pages / S3 / Any static host

Deploy all four files to any static host. `fetch('api-data.json')` will resolve correctly and auto-load on every page open. No server-side logic required.

---

## Pages & Features

### index.html — Catalog Viewer

The primary read-only catalog for all stakeholders.

**Group By** (toolbar across top of content area):

| Option | Groups APIs by |
|---|---|
| All APIs | No grouping — flat list |
| Tribe | Owning tribe |
| Application | Application context (CRM, OMS, PIM…) |
| Business Domain (L0) | L0 business capability |
| Capability (L1) | L1 capability area |
| Environment | Deployed environment (DEV, SIT, UAT, PROD) |
| API Layer | EAPI / PAPI / SAPI / EVENT / BATCH etc. |
| Migration Status | Not Started / In Analysis / Blocked / Complete |

**Sidebar filters** (combinable):
- Status (Active, Deprecated, Review)
- Migration Status
- Environment
- Migration Complexity (Low / Medium / High)
- Deployment Model (OnPrem / AWS / Hybrid)

**Search** — full-text across: API name, tags, squad name, application context, L0/L2 capability, upstream systems, consumers.

**Card view** — shows layer, deployment, environments, business capability breadcrumb, owning tribe + squad, migration status pill.

**Table view** — compact row-per-API with all key fields sortable.

**Detail drawer** (click any API card or row):
- Full technical profile
- Consumers (downstream) with per-entry environments, contract type, notes
- Upstream systems with per-entry environments, protocol, notes
- **Security COE tab** — auth scheme, TLS, scopes, policies, compliance flags, vault path, cert expiry, vulnerabilities
- **Solution Design COE tab** — architectural pattern, versioning, error handling, SLA, domain events, ADR links, technical debt
- **Operations COE tab** — on-call contact, uptime SLA, alerting threshold, maintenance window, monitoring links, runbooks, incident refs, known fragilities

---

### editor.html — Catalog Editor

Form-driven editor for maintaining `api-data.json`. No JSON hand-editing required.

**Sections per API:**

1. **Core Identity** — ID (auto), name, code repo/asset name, version, layer, protocol, status
2. **Infrastructure & Deployment** — runtime, Java version, deployment model, environments
3. **Ownership** — tribe, squad, application context, RAML/spec URL
4. **Business Capability Mapping** — L0 / L1 / L2 with autocomplete from existing values
5. **Integration Dependencies** — consumers (downstream) and upstream systems, each as a rich object with system name, environments, contract type/protocol, notes
6. **Migration Assessment** — migration status, complexity, tags
7. **CoE Metadata (tabbed)**:
   - Security COE — auth, TLS, scopes, policies, classification, compliance, vault, cert expiry, vulnerabilities
   - Solution Design COE — pattern, versioning, error handling, SLA, AsyncAPI spec, ADR links, domain events, technical debt
   - Operations COE — on-call, SLA, alerting, maintenance window, pipeline, monitoring links, runbooks, incidents, fragilities
8. **Documentation** — operational notes, Confluence links, design references
9. **Audit** — last reviewed by, last review date

**Key behaviours:**
- Unsaved changes indicator (amber dot) when any field is modified
- Save button commits to in-memory state
- **Export JSON** — downloads updated `api-data.json` AND must be the trigger to update the Git-committed version
- Delete with confirmation modal
- New API creates a timestamped unique ID automatically

> **Important:** The Export JSON button is the only way to persist changes. Saving in the editor saves to browser memory only — if you close the tab without exporting, changes are lost.

---

### dependencies.html — Dependency Visualiser

D3.js-powered visualisation page. Two tabs, shared tribe filter, shared theme toggle.

#### Tab 1 — Tribe Ownership Map (Icicle)

Zoomable icicle chart: **Integration COE → Tribe → Squad → API**

- Each cell is coloured by migration status
- Left accent bar on tribe cells coloured by tribe palette
- API cells show layer badge (EAPI/PAPI/SAPI) in corner
- Click a tribe or squad cell → zooms in to fill the canvas
- **Zoom out** button appears after zoom
- Click an API cell → side panel opens showing:
  - Layer, tribe, squad, deployment, migration status, runtime, data classification
  - Internal consumers (downstream APIs in catalog)
  - Internal upstream APIs (upstream APIs in catalog)
  - External systems touched (systems not matched to any catalog entry)
  - **Tribe readiness bar** — x of y APIs migrated, colored red/amber/green
- Tribe filter pills narrow the icicle to a single tribe — useful for per-tribe head presentations

#### Tab 2 — Dependency Graph

Force-directed graph with **swim lane constraints** by API layer:

```
EAPI     ────────────────────────────────────────
EVENT    ────────────────────────────────────────
PAPI     ────────────────────────────────────────
SAPI     ────────────────────────────────────────
BATCH    ────────────────────────────────────────
UTILITY  ────────────────────────────────────────
EXTERNAL ────────────────────────────────────────
```

- **Node colour** = migration status
- **Left bar on node** = tribe colour (identifies cross-tribe dependencies at a glance)
- **Solid edges** = internal API-to-API dependencies
- **Dashed edges** = connections to/from external systems
- **Arrows** show direction of dependency (source → target)
- Tribe filter narrows visible nodes; cross-tribe dependencies remain visible if they connect to focused APIs
- **Drag nodes** to reposition; zoom and pan the canvas

**Click any API node → side panel shows:**
- ⛔ **Must migrate first** — upstream internal APIs not yet Complete (sequencing blockers)
- ⚠ **Regression risk** — downstream APIs consuming this one, coloured by tribe (cross-tribe regression owners visible immediately)
- 🌐 **External systems touched** — carrier APIs, payment gateways, ERPs
- ⚡ **Known fragilities** from Operations COE block

**Click any external system node → side panel shows:**
- All catalog APIs that interact with that external system and their migration status

**Click same node again or click canvas background** → clears selection and resets all highlighting.

**Dependency resolution** — the graph uses fuzzy name matching to resolve whether a `consumers[].system` or `upstreamSystems[].system` string refers to an internal API. Matching rules (in priority order):
1. Exact name match (case-insensitive)
2. One name contains the other
3. Two or more significant words overlap

If a system name does not match any catalog API, it is treated as an external system node. To guarantee resolution for ambiguous names, keep `consumers[].system` values as close as possible to the target API's `name` field.

---

## Data Schema

### Top-level fields

```jsonc
{
  "meta": {
    "version": "1.2.0",
    "lastUpdated": "2026-03-07",
    "organization": "Integration COE",
    "catalogOwner": "Integration COE Lead"
  },
  "layerSuggestions": ["EAPI", "PAPI", "SAPI", "BATCH", "EVENT", "UTILITY", "FACADE"],
  "contractTypes": ["REST", "SOAP", "Kafka", "AsyncAPI", "GraphQL", "SFTP", "JMS", "Other"],
  "tribes": [ { "id": "tribe-cx", "name": "Customer Experience", "lead": "" } ],
  "businessCapabilities": [ { "l0": "Commerce", "l1": "Order Management", "l2": "Order Lifecycle" } ],
  "apis": [ /* see API entry below */ ]
}
```

`layerSuggestions` and `contractTypes` drive the datalist autocomplete in the editor. Add new values here to make them available as suggestions without changing any HTML.

### API entry fields

```jsonc
{
  "id": "api-001",                        // Unique — do not change after creation
  "name": "Customer Profile API",         // Business/display name
  "repoApiName": "customer-profile-api",  // Anypoint Exchange / Git repo asset name
  "version": "2.3.1",
  "layer": "EAPI",                        // Free text — use layerSuggestions as guide
  "protocol": "REST",
  "runtime": "MuleSoft 4.3",
  "javaVersion": "Java 8",
  "deploymentModel": "OnPrem",            // OnPrem | AWS | Azure | Hybrid | CloudHub
  "environments": ["DEV", "SIT", "UAT", "PROD"],
  "tribeId": "tribe-cx",                  // Must match a tribes[].id value exactly
  "businessCapability": {
    "l0": "Customer Management",
    "l1": "Customer Profile",
    "l2": "Identity & Auth"
  },
  "owningSquad": "Squad Alpha",
  "applicationContext": "CRM Portal",
  "ramlSpec": "https://anypoint.example.com/api/customer-profile",
  "consumers": [ /* see Consumer/Upstream entry below */ ],
  "upstreamSystems": [ /* see Consumer/Upstream entry below */ ],
  "status": "Active",                     // Active | Deprecated | Review | Inactive
  "migrationStatus": "Not Started",       // See Migration Status Values
  "migrationComplexity": "Medium",        // Low | Medium | High
  "confluenceLinks": [ { "label": "LLD", "url": "https://…" } ],
  "designReferences": [ { "label": "Sequence Diagram", "url": "https://…" } ],
  "operationalNotes": ["Free text note for Ops team"],
  "tags": ["customer", "identity", "core"],
  "lastReviewedBy": "john.doe@example.com",
  "lastReviewedDate": "2026-03-07",
  "security": { /* see Security COE block */ },
  "solutionDesign": { /* see Solution Design COE block */ },
  "operations": { /* see Operations COE block */ }
}
```

### Security COE block

```jsonc
"security": {
  "authScheme": "OAuth 2.0 (Client Credentials)",
  "oauthScopes": ["profile:read", "profile:write"],
  "tlsVersion": "TLS 1.2",               // TLS 1.2 | TLS 1.3 | TLS 1.1 (Deprecated)
  "gatewayPolicies": ["Rate Limiting", "JWT Validation", "IP Allowlist"],
  "dataClassification": "Confidential",   // Public | Internal | Confidential | Restricted
  "complianceFlags": ["GDPR"],            // GDPR | PCI-DSS | SOX | HIPAA etc.
  "secretsVaultPath": "/secret/prod/customer-profile",
  "certExpiry": "2026-09-01",             // ISO date — renders red/amber/green in viewer
  "knownVulnerabilities": ["Free text finding"]
}
```

`certExpiry` colour coding in the viewer: red = < 30 days, amber = < 90 days, green = > 90 days.

### Solution Design COE block

```jsonc
"solutionDesign": {
  "architecturalPattern": "Façade — aggregates CRM + Identity",
  "versioningStrategy": "URI versioning (/v2/)",
  "errorHandlingStrategy": "Standard error envelope with correlation-id",
  "slaTarget": "99.9% / < 500ms P95",
  "asyncApiSpec": "https://…",
  "adrLinks": [ { "label": "ADR-001 Auth Strategy", "url": "https://…" } ],
  "technicalDebt": ["No pagination on /customers/search"],
  "domainEvents": ["order.created", "order.cancelled"]
}
```

### Operations COE block

```jsonc
"operations": {
  "oncallContact": "squad-alpha@example.com",
  "monitoringLinks": [ { "label": "Datadog Dashboard", "url": "https://…" } ],
  "alertingThreshold": "Error rate > 2% over 5 min triggers P2",
  "maintenanceWindow": "Sundays 02:00–04:00 UTC",
  "runbookLinks": [ { "label": "Timeout Runbook", "url": "https://…" } ],
  "incidentRefs": ["INC-20241103 — SAP outage caused 45-min delay"],
  "knownFragilities": ["SAP BAPI single point of failure — no circuit breaker"],
  "pipelineLink": "https://jenkins.example.com/job/customer-profile-api",
  "uptimeSla": "99.9%"
}
```

### Consumer / Upstream entry

Both `consumers[]` and `upstreamSystems[]` use the same rich object format:

```jsonc
// Consumer (downstream — who calls this API)
{
  "system": "UXP Portal",
  "environments": ["UAT", "PROD"],
  "contractType": "REST",        // What protocol they use to call this API
  "notes": "Renders customer header — primary consumer"
}

// Upstream system (this API calls it)
{
  "system": "Salesforce CRM",
  "environments": ["PROD"],
  "protocol": "REST",            // What protocol this API uses to call upstream
  "notes": "Source of truth for customer master data"
}
```

> **Dependency graph resolution tip:** Keep the `system` value as close as possible to the target API's `name` field for internal APIs. Example: if the target API is named `"Inventory Stock SAPI"`, use `"Inventory Stock SAPI"` (not `"Inventory"` or `"WMS"`) in the upstream entry. Exact or near-exact matches resolve reliably; short abbreviations may not.

---

## Workflow — Updating the Catalog

```
1. Open editor.html
2. Load JSON → select api-data.json from your working copy
3. Select API from sidebar (or click + New for a new entry)
4. Edit fields across all sections and CoE tabs
5. Click 💾 Save Changes  (commits to in-memory state)
6. Click ⬇ Export JSON   (downloads updated api-data.json)
7. Replace api-data.json in your working copy with the downloaded file
8. Git commit & push
9. Team members pull and reload the file in their browser
```

This flow makes Git the audit trail for all catalog changes. The exported `api-data.json` contains an updated `meta.lastUpdated` timestamp automatically.

---

## Populating from Real Data

When migrating from the sample data to your real API landscape, work in this order:

**Step 1 — Tribes first**

Update the `tribes[]` array in `api-data.json` with your real tribe IDs and names before adding any APIs. Every API `tribeId` must reference a valid `tribes[].id`.

**Step 2 — Business capabilities**

Populate `businessCapabilities[]` with your organisation's L0/L1/L2 taxonomy. These drive the autocomplete in the editor's Business Capability Mapping section.

**Step 3 — APIs — core fields first**

For each API, populate these minimum fields to get functional views immediately:
- `id`, `name`, `layer`, `tribeId`, `status`, `migrationStatus`, `migrationComplexity`
- `environments`, `deploymentModel`, `runtime`, `javaVersion`
- `businessCapability` (L0/L1/L2)

**Step 4 — Dependencies**

Populate `consumers[]` and `upstreamSystems[]` for each API. This is what powers the dependency graph. Take care with system names — see the resolution tip above.

**Step 5 — CoE metadata**

Fill Security, Solution Design and Operations blocks. These can be done incrementally — all fields are optional. Missing fields display as `—` in the viewer.

**Bulk population tip:** If you have an existing spreadsheet or Anypoint Exchange export, it is faster to populate `api-data.json` directly in a text editor than to use the editor UI for bulk entry. Run the result through [jsonlint.com](https://jsonlint.com) before loading to catch syntax errors.

---

## Tribe & Spotify Model Mapping

The catalog implements the Spotify model with **Tribes, Squads and Chapters** (no Guilds).

| Catalog field | Spotify concept | Notes |
|---|---|---|
| `tribes[].id` / `tribes[].name` | Tribe | Owning domain tribe |
| `tribes[].lead` | Tribe Lead | Optional — populate as team grows |
| `api.tribeId` | Tribe ownership | Links API to tribe |
| `api.owningSquad` | Squad | Free text — no squad master list required |
| `api.applicationContext` | Product/application context | What system this API serves |

Chapters (e.g. "Integration Chapter", "Security Chapter") map to the CoE roles — Security COE, Solution Design COE, Operations COE — and are represented through the three CoE metadata blocks rather than as a structural field.

---

## Migration Status Values

| Value | Meaning | Colour |
|---|---|---|
| `Not Started` | Not yet assessed or planned | Indigo |
| `In Analysis` | Being assessed — complexity, effort, dependencies mapped | Amber |
| `In Progress` | Actively being migrated | Cyan |
| `Blocked` | Cannot proceed — dependency, commercial, or technical blocker | Red |
| `Complete` | Migrated to MuleSoft 4.9 / Java 17 | Green |
| `Decommission Candidate` | To be retired rather than migrated | Grey |

In the dependency graph, an API with upstream internal APIs not yet `Complete` will show those as blockers in the click panel. This is the primary tool for sequencing migration waves.

---

## Theme

Both `index.html`, `editor.html` and `dependencies.html` support dark and light themes. The preference is persisted in `localStorage` under the key `coe-theme` and is shared across all three pages (same browser, same origin).

Toggle via the 🌙 / ☀️ button in the header of any page.

The Export JSON button in `editor.html` is intentionally a **static amber/yellow** (`#f59e0b`) — it does not change with theme, making it visually distinct as the primary action regardless of which theme is active.

---

## Extending the Catalog

### Adding a new Group By dimension

In `index.html`, find the `groupby-bar` div and add a new button:

```html
<button class="groupby-btn" onclick="setGroupBy('myfield')">My Grouping</button>
```

Then in the `groupAPIs()` function, add a new `else if` branch:

```js
else if (GROUP_BY === 'myfield') key = api.myField || 'Unknown';
```

Add the corresponding field to each API entry in `api-data.json`.

### Adding a new API layer type

Add the new value to `layerSuggestions` in `api-data.json`:

```json
"layerSuggestions": ["EAPI", "PAPI", "SAPI", "BATCH", "EVENT", "UTILITY", "FACADE", "MYTYPE"]
```

It will appear as an autocomplete suggestion in the editor immediately. The viewer badge will fall back to a neutral grey style for unrecognised layer values. To add a specific colour, add a CSS rule to `index.html`:

```css
.badge-layer-MYTYPE { background: rgba(x,y,z,0.08); border-color: rgba(x,y,z,0.3); color: #hexcolor; }
```

The dependency graph swim lane will position the new layer between existing lanes alphabetically. To control its vertical position, add it to the `LAYERS` array in `renderGraph()` at the desired position.

### Adding a new CoE metadata section

1. Add the new block to each API entry in `api-data.json` (e.g. `"testingCoe": { ... }`)
2. In `editor.html`, add a new `<button class="coe-tab">` and `<div class="coe-panel">` inside the CoE tabs section
3. Add field initialisers in `renderEditor()` after the existing CoE initialisers
4. Add save logic in `saveAPI()` for `api.testingCoe = { ... }`
5. In `index.html`, add a new `<button class="cvtab">` and `<div class="cvpanel">` in the drawer's CoE section
6. Add a `renderCoeSection()` call for the new tab

---

## Known Constraints

**Browser file:// restriction** — `api-data.json` will not auto-load when files are opened directly from the filesystem. Use a local server (`python3 -m http.server 8080`) or the manual Load JSON button.

**Dependency graph name resolution** — cross-API dependency edges are resolved by fuzzy name matching, not by explicit ID references. Short or abbreviated system names in `consumers[].system` / `upstreamSystems[].system` may not resolve correctly. Use names close to the target API's `name` field, or add an optional `apiId` field for hard references (future enhancement).

**No authentication** — the tool is designed for internal team use from a shared folder or static host. It does not implement any access control. Do not host publicly without adding appropriate access restrictions if the catalog contains sensitive security or compliance information.

**Browser localStorage scope** — `localStorage` is scoped per origin. Under `file://` protocol, different folder paths may be treated as different origins by some browsers. Theme preference may not persist between different folder locations.

**Single-file architecture** — all CSS and JS are inline in each HTML file. This keeps the tool portable (copy four files, it works) but means style and logic changes must be applied to each file separately.

---

## Roadmap / Future Considerations

These are items identified during the initial build that have been deferred deliberately:

- **Explicit `apiId` on consumer/upstream entries** — replace fuzzy name matching with hard ID references for guaranteed dependency graph resolution
- **GitHub Pages / S3 deployment** — serve the folder from a static host so `api-data.json` auto-loads without a local server
- **Export to CSV / Excel** — for stakeholders who prefer spreadsheet views of the catalog
- **Migration wave planner** — group APIs into sequenced migration waves based on dependency chain analysis, with wave-level effort estimates
- **Anypoint Exchange integration** — pull API metadata directly from the MuleSoft Anypoint Platform API rather than hand-populating
- **Confluence export** — generate a Confluence-compatible page from an API's drawer content
- **COE review workflow** — flag APIs as "pending Security COE review", "pending Solution Design sign-off" etc. with reviewer assignment
