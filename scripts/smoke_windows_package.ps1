param(
    [string]$PackageRoot = (Join-Path $PSScriptRoot '..\dist\New-Earth-Engineering-OS-Windows-v1.3.0'),
    [int]$TimeoutSeconds = 60
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$packagePath = (Resolve-Path $PackageRoot).Path
$desktopExe = Join-Path $packagePath 'NEOS.exe'
if (-not (Test-Path $desktopExe)) {
    throw "Desktop executable not found: $desktopExe"
}

$settingsPath = Join-Path $env:LOCALAPPDATA 'New Earth Engineering OS\desktop-settings.json'
$servicePort = 8765
if (Test-Path $settingsPath) {
    try {
        $settings = Get-Content $settingsPath -Raw | ConvertFrom-Json
        if ($settings.service_port) {
            $servicePort = [int]$settings.service_port
        }
    } catch {
        Write-Host "Unable to parse settings file: $settingsPath"
    }
}

$logPath = Join-Path $env:LOCALAPPDATA 'New Earth Engineering OS\logs\neos-desktop.log'
if (Test-Path $logPath) {
    Remove-Item $logPath -Force
}

$desktop = Start-Process -FilePath $desktopExe -WorkingDirectory $packagePath -PassThru

$deadline = (Get-Date).ToUniversalTime().AddSeconds($TimeoutSeconds)
$health = $null
while ((Get-Date).ToUniversalTime() -lt $deadline) {
    if ($desktop.HasExited) {
        break
    }
    try {
        $health = Invoke-RestMethod -Uri "http://127.0.0.1:$servicePort/health" -TimeoutSec 2
        if ($health.status -eq 'healthy') {
            break
        }
    } catch {
        Start-Sleep -Milliseconds 500
    }
}

function Get-DesktopWindowHandle {
    param(
        [int]$ProcessId,
        [int]$WaitMilliseconds = 0
    )

    $deadline = (Get-Date).ToUniversalTime().AddMilliseconds($WaitMilliseconds)
    do {
        $liveDesktop = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
        if ($liveDesktop -and $liveDesktop.MainWindowHandle -ne 0) {
            return [int]$liveDesktop.MainWindowHandle
        }
        Start-Sleep -Milliseconds 250
    } while ((Get-Date).ToUniversalTime() -lt $deadline)

    return 0
}

Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;

public static class Win32WindowTools {
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

    [DllImport("user32.dll")]
    public static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);

    [DllImport("user32.dll")]
    public static extern bool IsWindowVisible(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);

    [DllImport("user32.dll", SetLastError = true)]
    public static extern bool PostMessage(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam);
}
"@ -ErrorAction SilentlyContinue | Out-Null

$mainWindowHandle = Get-DesktopWindowHandle -ProcessId $desktop.Id -WaitMilliseconds 15000
if ($mainWindowHandle -eq 0) {
    $handles = New-Object System.Collections.Generic.List[IntPtr]
    [void][Win32WindowTools]::EnumWindows({
        param([IntPtr]$hWnd, [IntPtr]$lParam)
        $pid = 0
        [void][Win32WindowTools]::GetWindowThreadProcessId($hWnd, [ref]$pid)
        if ($pid -eq $desktop.Id -and [Win32WindowTools]::IsWindowVisible($hWnd)) {
            $handles.Add($hWnd) | Out-Null
        }
        return $true
    }, [IntPtr]::Zero)
    if ($handles.Count -gt 0) {
        $mainWindowHandle = [int]$handles[0]
    }
}

$closeSent = $false
if (-not $desktop.HasExited) {
    if ($mainWindowHandle -ne 0) {
        $desktop.Refresh()
        $closeSent = $desktop.CloseMainWindow()
        if (-not $closeSent) {
            $closeSent = [Win32WindowTools]::PostMessage([IntPtr]$mainWindowHandle, 0x0010, [IntPtr]::Zero, [IntPtr]::Zero)
        }
    } else {
        Write-Host 'No visible main window handle was discovered for the desktop process.'
    }
}

$exitDeadline = (Get-Date).ToUniversalTime().AddSeconds($TimeoutSeconds)
while ((Get-Date).ToUniversalTime() -lt $exitDeadline) {
    if ($desktop.HasExited) {
        break
    }
    Start-Sleep -Milliseconds 250
}

$cleanupDeadline = (Get-Date).ToUniversalTime().AddSeconds(15)
$ownedBackendStillRunning = $null
while ((Get-Date).ToUniversalTime() -lt $cleanupDeadline) {
    $ownedBackendStillRunning = Get-CimInstance Win32_Process -Filter "Name='neos_engine.exe'" |
        Where-Object { $_.CommandLine -like "*--owner-pid $($desktop.Id)*" }
    if (-not $ownedBackendStillRunning) {
        break
    }
    Start-Sleep -Milliseconds 250
}

$ownedBackendStillRunning = Get-CimInstance Win32_Process -Filter "Name='neos_engine.exe'" |
    Where-Object { $_.CommandLine -like "*--owner-pid $($desktop.Id)*" }

$summary = [pscustomobject]@{
    package_root = $packagePath
    desktop_pid = $desktop.Id
    desktop_alive = -not $desktop.HasExited
    service_port = $servicePort
    backend_health = $health
    main_window_handle = $mainWindowHandle
    close_sent = $closeSent
    desktop_exited = $desktop.HasExited
    owned_backend_still_running = [bool]$ownedBackendStillRunning
}

$summary | ConvertTo-Json -Depth 8

if ($null -eq $health -or $health.status -ne 'healthy') {
    Write-Host '--- LOG TAIL ---'
    if (Test-Path $logPath) {
        Get-Content $logPath -Tail 120
    }
    exit 1
}

if (-not $closeSent -or -not $desktop.HasExited -or $ownedBackendStillRunning) {
    Write-Host '--- LOG TAIL ---'
    if (Test-Path $logPath) {
        Get-Content $logPath -Tail 120
    }
    exit 1
}

exit 0
