Get-ChildItem -Recurse -File -Filter *.py |
Where-Object { $_.FullName -notmatch '\\(venv|__pycache__)\\' } |
Select-String -Pattern '\bmodels\b|\breports\b' |
Select-Object Path, LineNumber, Line