# ADR-005: Using GitHub for Project Hosting

**Status:** Accepted
**Date:** 2026-04-05

## Context

The project needs a publicly accessible remote repository with issue tracking,
pull request workflow, and CI/CD capabilities. GitHub is the dominant platform
for open-source Python libraries and integrates directly with GitHub Actions
and GitHub Pages (used for documentation hosting).

## Decision

Host the project on GitHub at `github.com/Philipp-IoT/fnirsi_protocol`.
GitHub Pages serves the MkDocs-generated documentation site.

## Consequences

- **Positive:** Free hosting for public repositories; GitHub Actions and
  Pages included at no cost.
- **Positive:** Discoverability for potential contributors.
- **Negative:** Vendor lock-in to GitHub platform; migration would require
  reconfiguring CI, Pages, and all external links.
