# Persistence Evidence

The registry uses the existing SQLite-backed project and scan tables.

Observed persistence posture:

- no new migration was required
- no schema bump was introduced
- the feature is derived from already persisted project and scan data
