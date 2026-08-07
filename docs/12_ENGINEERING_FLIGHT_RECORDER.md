# Engineering Flight Recorder Concept

The Engineering Flight Recorder records significant project events over time: commits, builds, tests, scans, releases, decisions and validated experiments.

The goal is to reconstruct project evolution and answer questions such as:
- What changed before a regression appeared?
- Which evidence supported release approval?
- When did a dependency enter the product?
- Which decisions shaped the current architecture?

The recorder should store metadata and references rather than indiscriminately duplicating entire development environments.
