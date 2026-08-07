param([string]$Repo = "D:\Dev\Projects\MicroGrow V1")
$ErrorActionPreference = "Stop"
& .\.venv\Scripts\python.exe -m neos init-project --manifest examples\microgrow\project.neos.json
& .\.venv\Scripts\python.exe -m neos scan --project-id microgrow-v1 --repo $Repo
& .\.venv\Scripts\python.exe -m neos project-summary --project-id microgrow-v1
