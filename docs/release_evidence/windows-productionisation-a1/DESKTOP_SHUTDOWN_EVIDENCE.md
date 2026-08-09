# Desktop Shutdown Evidence

Observed on 2026-08-07.

## Final packaged smoke

Command:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\smoke_windows_package.ps1
```

Observed summary:

- `desktop_exited: true`
- `close_sent: true`
- `owned_backend_still_running: false`
- `backend_health.status: healthy` before close

## Backend smoke

Command:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\smoke_windows_backend.ps1 -ShutdownAfterCheck
```

Observed summary:

- `alive: false`
- `listener: false`
- shutdown returned an expected transport close error after the service stopped responding

## Conclusion

The packaged desktop now closes cleanly and does not leave its owned backend behind.
