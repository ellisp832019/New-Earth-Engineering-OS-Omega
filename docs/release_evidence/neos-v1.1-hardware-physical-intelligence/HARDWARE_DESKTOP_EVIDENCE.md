# Hardware Desktop Evidence

The desktop app includes Hardware Centre in the navigation and renders hardware payloads from the backend.

Observed validation:

- `flutter analyze` passed
- `flutter test` passed
- `scripts\\smoke_windows_package.ps1` passed against the final `v1.1.0` package

Desktop-side coverage includes:

- Hardware Centre navigation entry
- project hardware payload loading
- hardware summary and raw payload panels

The desktop UI remains thin and read-only over the backend snapshot.
