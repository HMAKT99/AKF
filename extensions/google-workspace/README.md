# AKF — Google Workspace Add-on

Trust metadata viewer, embedder, and auditor for Google Docs, Sheets, and Slides.

## Features

- **AKF menu** in Docs, Sheets, and Slides (View Trust, Run Audit, Embed Metadata)
- **Sidebar** with tabbed UI — Overview, Claims, Provenance, Audit, Detection
- **Card Service homepage** for the add-on panel
- **7 compliance checks** with score and recommendations
- **10 AI-specific detection classes** (hallucination risk, knowledge laundering, trust degradation, etc.)
- **Claim creation** — add claims with confidence, source attribution, and AI risk tagging
- Metadata stored via `DocumentProperties` (persists within Google Workspace)

## Deploy

### 1. Install clasp

```bash
npm install -g @google/clasp
clasp login
```

### 2. Create an Apps Script project

```bash
clasp create --type standalone --title "AKF Trust Metadata"
```

This generates `.clasp.json` with your project's `scriptId`.

### 3. Push the code

```bash
cd extensions/google-workspace
clasp push
```

### 4. Test

```bash
clasp open
```

In the Apps Script editor, click **Deploy** → **Test deployments** → select a Google Doc/Sheet/Slide to test with.

### 5. Publish to Google Workspace Marketplace

1. Set up a [GCP project](https://console.cloud.google.com/) and link it to the Apps Script project
2. Configure the OAuth consent screen
3. Submit via the [Google Workspace Marketplace SDK](https://developers.google.com/workspace/marketplace/how-to-publish)

## Architecture

- `Code.gs` — entry point: menu setup, sidebar launcher, Card homepage trigger
- `AKF.gs` — metadata storage (`DocumentProperties`), embed logic, 7-check audit, 10 detection classes, trust computation
- `Cards.gs` — Card Service UI for homepage, claims list, audit results, detection card
- `Sidebar.html` — rich sidebar with tabs (Overview, Claims, Provenance, Audit, Detection), claim creation form, dark theme

## Note

Document Properties don't survive export to `.docx`. For DOCX interop, use the Python CLI (`akf embed`) to re-embed after export.
