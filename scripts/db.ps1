param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("upgrade", "current", "history", "check")]
    [string]$Command
)

Set-Location (Split-Path $PSScriptRoot -Parent)
python -m backend.cli db $Command
