# Settings

Observed on 2026-08-07.

## Settings file

The desktop shell stores local settings at:

- `%LOCALAPPDATA%\New Earth Engineering OS\desktop-settings.json`

## Stored fields

The current settings payload includes:

- `data_directory`
- `service_host`
- `service_port`
- `auto_refresh`
- `prefer_bundled_backend`
- `recent_project_id`

## Defaults

The default settings are:

- data directory under `%LOCALAPPDATA%\New Earth Engineering OS`
- service host `127.0.0.1`
- service port `8765`
- auto refresh enabled
- bundled backend preferred
- no recent project id

## Behavior

The desktop shell creates the settings file if it does not exist, keeps reading resilient to unreadable JSON, and persists the resolved service port after a successful startup.

## Operational note

Changing `service_host` or `service_port` is only useful when intentionally attaching to a non-default local service. For normal use, the bundled backend and default loopback settings are the safest choice.
