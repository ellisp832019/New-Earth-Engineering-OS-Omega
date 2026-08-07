# Troubleshooting

## Python not found
Install Python 3.11+ and ensure `python` is on PATH.

## PowerShell blocks script
Use `Set-ExecutionPolicy -Scope Process Bypass` for the current terminal session.

## Unknown project
Run `init-project` before `scan`.

## Wrong repository path
Pass an absolute path to `--repo`.

## Reset local Alpha database
Delete `.neos/neos.db` only if you intentionally want to discard local NEOS state.
