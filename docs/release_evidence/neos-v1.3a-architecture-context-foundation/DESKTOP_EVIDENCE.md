# Desktop Evidence

The desktop app now includes a Registry Centre entry in the navigation and workspace area.

Observed behavior:

- the registry view renders the registry snapshot
- it shows identity, contracts, drift, impact, conflicts, and sources
- it reuses the existing project payload plumbing
- the Windows package smoke check confirmed the launcher, backend ownership, and Registry Centre remain intact on the integrated `main` build `e4ea2bd44ace4e330bf5b50c4dbb1e0ebb37cd92`
