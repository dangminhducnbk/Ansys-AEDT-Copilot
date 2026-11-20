# Feature Specification: Config Save overwrites the generated file (no path picking)

**Feature Branch**: `main` (no branch; repo owner works on main)

**Created**: 2026-11-16

**Status**: Accepted (local link approved by the user 2026-11-16)

**Input**: User description: "khi người dùng nhập tên và bấm save trong config file, nó save đè lên file được tạo ra,
không cần người dùng chọn lại đường dẫn."

## Context

5.0.0 (feature 038): the tool writes `<request folder>/config.html`; the user opens it, fills the channel folder name
and presses Save. Today Save asks for a file location the first time (browser save dialog) or downloads a copy to the
Downloads folder; the tool then looks for the newest saved copy. The user must find and pick the request folder by hand,
and a wrong pick leaves a stray copy.

A web page opened directly from disk cannot overwrite its own file without the user picking it (browser security).
To save with no picking, the page must be served by the tool on this PC, and the tool writes the file.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Save writes straight to the generated config file (Priority: P1)

The tool gives the user a link to the config page. The user opens it, fills every channel folder name, presses Save:
the page says "Saved to <request folder>\config.html" with the time; no dialog, no download. The next tool step
(config check) reads exactly that file.

**Why this priority**: it is the whole request.

**Independent Test**: on a board copy request, open the config link, fill the folder names, press Save; the generated
`config.html` changes (new saved time, same path), no file appears in Downloads, no dialog was shown; config check
reads the values.

**Acceptance Scenarios**:

1. **Given** the config page opened from the tool's link, **When** the user presses Save with valid folder names,
   **Then** the generated file is overwritten in place within 2 s and the page shows the path and time.
2. **Given** a channel folder field is empty or invalid, **When** Save is pressed, **Then** nothing is written and the
   page shows the 038 message ("Not saved: fill the channel folder of …").
3. **Given** the user saves twice, **When** config check runs, **Then** it uses the last save.

---

### User Story 2 - Clear message when the page cannot save (Priority: P2)

If the tool is not running (Claude closed) or the page was opened another way (double-click on the file), Save cannot
reach the tool. The page says so in one line and falls back to the 038 behaviour (save dialog or download), which the
tool still reads.

**Why this priority**: the user never loses edits, but this is the exception path.

**Independent Test**: stop the tool, press Save on the open page; the message appears and the 038 fallback runs.

**Acceptance Scenarios**:

1. **Given** the tool is not reachable, **When** Save is pressed, **Then** the page shows "Cannot reach the tool —
   saving with the browser instead" and uses the 038 fallback.

---

### Edge Cases

- Page of an older request opened from the link: Save writes only to that request's own config file; a page can never
  write to another path (the tool decides the path from the request, not from the page).
- Two browser tabs of the same page: the last Save wins; the page shows the saved time so the user sees which one.
- The request already passed the cut (channel config page is read-only, 038): Save is not offered.
- The file was changed on disk after the page was opened (tool rewrote it after isim_config again): Save warns that a
  newer version exists and asks the user to reload (no silent overwrite of a newer page).
- Port in use / security: the save service listens only on this PC (not the network) and accepts saves only for open
  requests.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001** The tool provides the config page through a local link (this PC only) for every open request; message M1
  gives this link in addition to the file path.
- **FR-002** Save on a page opened from the link sends the page content to the tool, which overwrites
  `<request folder>/config.html` (path chosen by the tool from the request id) — no dialog, no download.
- **FR-003** Save keeps the 038 rules: refused while any channel folder name is missing / invalid; saved content is the
  same format the config check already reads.
- **FR-004** After a successful save the page shows the full file path and the save time; on failure it shows the
  reason in one line.
- **FR-005** When the tool cannot be reached, Save falls back to the 038 behaviour (browser save dialog, else download)
  and says so; config check still finds that copy (038 reader unchanged).
- **FR-006** Save is refused (with a reload message) when the file on disk is newer than the version the page was
  opened from.
- **FR-007** The local service accepts connections from this PC only and writes only the config file of a known,
  not-finished request; nothing else on disk can be written through it.
- **FR-008** Guide / M1 text: "Mở link, điền tên folder, bấm Save rồi trả lời *xong*" / "Open the link, fill the folder
  names, press Save, then reply *done*" (Vietnamese + English, pasted verbatim).

### Key Entities

- **Config page link**: local address of one request's config page; valid while the tool runs.
- **Saved config**: the generated `config.html` with the saved state and saved time (038 format).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001** In the normal path the user presses Save with zero dialogs and zero file-location choices (checked on a
  board copy in the browser).
- **SC-002** After Save, the generated file holds the new state in 100 % of tests and no copy is created in Downloads.
- **SC-003** Config check after a link Save reads the saved values with no search of other folders.
- **SC-004** A save request for a path or request that is not an open request is refused in 100 % of tests.

## Assumptions

- The tool (MCP server) runs on the same PC as the browser while the user edits the config (normal Claude desktop use).
- The browser is the user's default browser (Chrome / Edge); no extension is needed.
- The 038 page layout, fields and validation stay the same; only the Save target changes.
- Requests created by 5.0.0 get the link too (their config file path is known).
