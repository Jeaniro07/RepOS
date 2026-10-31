<#
One-command installer for the anti-slop video toolkit on Windows 10/11.

  irm https://raw.githubusercontent.com/Jeaniro07/RepOS/main/install.ps1 | iex

To pass options, download first:
  irm https://raw.githubusercontent.com/Jeaniro07/RepOS/main/install.ps1 -OutFile install.ps1
  powershell -ExecutionPolicy Bypass -File .\install.ps1 -Ref main -NoTest

What it does: installs Git and Python 3.12 with winget when they are missing, clones or updates
the repo into %USERPROFILE%\antislop\RepOS, downloads a static ffmpeg 8.1 build (BtbN, GPL) into
%LOCALAPPDATA%\slopguard\bin, puts a `slopguard` command there and adds that folder to your user
PATH, then runs `slopguard doctor` and the test suite. It never asks for or stores any API key.
#>
[CmdletBinding()]
param(
    [string]$Ref = "main",
    [string]$Dir = (Join-Path $HOME "antislop\RepOS"),
    [string]$FfmpegRelease = "8.1",
    [switch]$NoTest,
    [switch]$NoWinget
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"   # Invoke-WebRequest is much faster without the progress bar
[Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
$RepoUrl = "https://github.com/Jeaniro07/RepOS"
$Bin = Join-Path $env:LOCALAPPDATA "slopguard\bin"

function Say($msg) { Write-Host ""; Write-Host "==> $msg" -ForegroundColor Cyan }
function Have($cmd) { [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }

function Refresh-Path {
    $machine = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $user = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$machine;$user;$Bin"
}

function Find-Python {
    # Prefer the py launcher; skip the Microsoft Store "python" alias, which only opens the Store.
    $candidates = @(@("py", "-3"), @(,"python"), @(,"python3"))
    foreach ($c in $candidates) {
        $exe = $c[0]
        if (-not (Have $exe)) { continue }
        $src = (Get-Command $exe).Source
        if ($src -like "*\WindowsApps\*") { continue }
        $extra = @()
        if ($c.Count -gt 1) { $extra = @($c[1..($c.Count - 1)]) }
        try {
            $ok = & $exe @extra -c "import sys; print(1 if sys.version_info >= (3, 10) else 0)" 2>$null
            if ($LASTEXITCODE -eq 0 -and "$ok".Trim() -eq "1") {
                # The leading comma keeps a one-element array from being unrolled into a string.
                return ,(@($exe) + $extra)
            }
        } catch { }
    }
    return $null
}

function Winget-Install($id) {
    if ($NoWinget -or -not (Have "winget")) {
        throw "Missing $id and winget is not available. Install it manually, then re-run this script."
    }
    Say "Installing $id with winget"
    winget install --id $id -e --silent --accept-package-agreements --accept-source-agreements --scope user
    if ($LASTEXITCODE -ne 0) {
        # Some packages only offer a machine-wide installer.
        winget install --id $id -e --silent --accept-package-agreements --accept-source-agreements
    }
    Refresh-Path
}

Say "Checking prerequisites"
Refresh-Path
if (-not (Have "git")) { Winget-Install "Git.Git" }
if (-not (Have "git")) { throw "git is still not on PATH. Open a new PowerShell window and re-run." }
$Python = Find-Python
if (-not $Python) {
    Winget-Install "Python.Python.3.12"
    $Python = Find-Python
}
if (-not $Python) { throw "Python 3.10+ is still not found. Open a new PowerShell window and re-run." }
$PyExe = $Python[0]
$PyArgs = @()
if ($Python.Count -gt 1) { $PyArgs = @($Python[1..($Python.Count - 1)]) }
$pyVersion = & $PyExe @PyArgs -c "import platform; print(platform.python_version())"
Write-Host "git: $((git --version) -replace 'git version ', '')  python: $pyVersion ($($Python -join ' '))"

Say "Getting $RepoUrl ($Ref) into $Dir"
if (Test-Path (Join-Path $Dir ".git")) {
    git -C $Dir fetch --depth 1 origin $Ref
    if ($LASTEXITCODE -ne 0) { throw "git fetch failed" }
    git -C $Dir checkout -q -B $Ref FETCH_HEAD
} else {
    New-Item -ItemType Directory -Force -Path (Split-Path $Dir) | Out-Null
    git clone --depth 1 --branch $Ref $RepoUrl $Dir
    if ($LASTEXITCODE -ne 0) { throw "git clone failed" }
}

Say "Installing ffmpeg into $Bin"
New-Item -ItemType Directory -Force -Path $Bin | Out-Null
$haveOwn = (Test-Path (Join-Path $Bin "ffmpeg.exe")) -and (Test-Path (Join-Path $Bin "ffprobe.exe"))
if (-not $haveOwn) {
    $tmp = Join-Path ([IO.Path]::GetTempPath()) ("slopguard-" + [Guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Force -Path $tmp | Out-Null
    $zip = Join-Path $tmp "ffmpeg.zip"
    $assets = @("ffmpeg-n$FfmpegRelease-latest-win64-gpl-$FfmpegRelease.zip", "ffmpeg-master-latest-win64-gpl.zip")
    $got = $false
    foreach ($a in $assets) {
        $url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/$a"
        Write-Host "downloading $url (about 150 MB)..."
        for ($try = 1; $try -le 3 -and -not $got; $try++) {
            try { Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing; $got = $true }
            catch { Write-Host "  attempt $try failed: $($_.Exception.Message)"; Start-Sleep -Seconds (3 * $try) }
        }
        if ($got) { break }
    }
    if (-not $got) { throw "Could not download ffmpeg. Check your connection and re-run." }
    Expand-Archive -Path $zip -DestinationPath $tmp -Force
    foreach ($name in @("ffmpeg.exe", "ffprobe.exe")) {
        $found = Get-ChildItem -Path $tmp -Recurse -Filter $name | Where-Object { $_.DirectoryName -like "*\bin" } | Select-Object -First 1
        if (-not $found) { throw "$name not found in the downloaded archive" }
        Copy-Item $found.FullName (Join-Path $Bin $name) -Force
    }
    Remove-Item -Recurse -Force $tmp
}
& (Join-Path $Bin "ffmpeg.exe") -hide_banner -version | Select-Object -First 1

Say "Creating the slopguard command"
$toolkit = Join-Path $Dir "toolkit"
$pyLine = ($Python | ForEach-Object { if ($_ -match '\s') { '"' + $_ + '"' } else { $_ } }) -join ' '
$shim = @"
@echo off
set "PYTHONPATH=$toolkit;%PYTHONPATH%"
$pyLine -m slopguard %*
"@
Set-Content -Path (Join-Path $Bin "slopguard.cmd") -Value $shim -Encoding ASCII

$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if (-not $userPath) { $userPath = "" }
if (($userPath -split ';') -notcontains $Bin) {
    [Environment]::SetEnvironmentVariable("Path", ($userPath.TrimEnd(';') + ";" + $Bin).TrimStart(';'), "User")
    Write-Host "Added $Bin to your user PATH (new terminals pick it up)."
}
Refresh-Path

Say "slopguard doctor"
& (Join-Path $Bin "slopguard.cmd") doctor
if ($LASTEXITCODE -ne 0) { throw "slopguard doctor reported a problem (see above)." }

if (-not $NoTest) {
    Say "Self-test"
    Push-Location $toolkit
    try {
        & $PyExe @PyArgs -m unittest discover -s tests
        if ($LASTEXITCODE -ne 0) { throw "Some tests failed (see above)." }
    } finally { Pop-Location }
}

Write-Host ""
Write-Host "Done. slopguard is installed." -ForegroundColor Green
Write-Host "  Repo:    $Dir"
Write-Host "  Try:     slopguard doctor"
Write-Host "           slopguard lint-script `"$Dir\examples\kopi-pahit\script-slop.md`""
Write-Host "  Rakazo:  Integrations > + > From GitHub > $RepoUrl/tree/$Ref/rakazo-plugin"
Write-Host "  Open a new terminal so the updated PATH applies."
