param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Arguments
)

python (Join-Path $PSScriptRoot "run.py") @Arguments
