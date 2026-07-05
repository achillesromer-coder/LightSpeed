# Morpheus Floor

**Z-Level:** -1
**Version:** 5.1.2
**Status:** Active smart floor

Morpheus owns review, proofing, file editing, knowledge previews, and code-analysis
surfaces. The active UI coordinator is the root floor module `Z Axis/Morpheus.py`;
this folder holds the owned review/editor components and floor-local data.

## Canonical Ownership

- `components/drag_drop_interface.py`: file intake/review surface.
- `components/rich_text_editor.py`: markdown and document editing surface.
- `components/chat_archive_browser.py`: chat/archive browsing surface for reviewed knowledge.
- `components/morpheus_portal_glass.py`: glass preview and review portal.
- `data/`: review outputs, promoted excerpts, and floor-local proofing state when generated.

## Current Runtime Flow

Oracle owns proofed knowns and catalog state. Morpheus reviews, previews, and edits
those materials before they become library, encyclopedia, datatable, or scenario-lab
objects. Smith handles queued jobs, Neo proposes bounded actions, and Architect
governs publish decisions.

## Reduction Policy

Do not add duplicate floor-local entrypoints here. Add new user-facing behavior to
the root coordinator or runtime bridge, and keep floor-local files focused on review
components, editors, previews, and proofing data.
