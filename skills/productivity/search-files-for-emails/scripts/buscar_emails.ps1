param([string]$Path = "F:\Rescate_Raw_Rec")

$EmailPattern = '\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
$Results = @()
$Stats = @{txt=0; docx=0; doc=0; xlsx=0; xls=0; pdf=0; total=0}

Write-Output "=== BUSCADOR DE EMAILS v1.2 ==="
Write-Output "Ruta: $Path"
Write-Output ""

# --- 1. TEXTOS PLANOS ---
Write-Output "[1/5] Escaneando TXT/HTML/XML..."
Get-ChildItem $Path -Recurse -Include '*.txt','*.html','*.xml','*.ini' | ForEach-Object {
    $Stats.total++; $Stats.txt++
    $m = Select-String -Path $_.FullName -Pattern $EmailPattern -AllMatches
    if ($m) {
        $Results += [PSCustomObject]@{File=$_.Name; Folder=$_.Directory.Name; Tipo='TXT'; Emails=($m.Matches.Value | Select-Object -Unique) -join ', '}
    }
}

# --- 2. DOCX ---
Write-Output "[2/5] Escaneando DOCX..."
Add-Type -AssemblyName System.IO.Compression.FileSystem
Get-ChildItem $Path -Recurse -Filter '*.docx' | ForEach-Object {
    $Stats.total++; $Stats.docx++
    try {
        $zip = [System.IO.Compression.ZipFile]::OpenRead($_.FullName)
        $entry = $zip.GetEntry('word/document.xml')
        if ($entry) {
            $r = New-Object System.IO.StreamReader($entry.Open())
            $xml = $r.ReadToEnd(); $r.Close()
            $text = [Regex]::Replace($xml, '<[^>]+>', ' ')
            $text = [System.Web.HttpUtility]::HtmlDecode($text)
            $m = [Regex]::Matches($text, $EmailPattern)
            if ($m.Count -gt 0) {
                $Results += [PSCustomObject]@{File=$_.Name; Folder=$_.Directory.Name; Tipo='DOCX'; Emails=($m.Value | Select-Object -Unique) -join ', '}
            }
        }
        $zip.Dispose()
    } catch {}
}

# --- 3. DOC ---
Write-Output "[3/5] Escaneando DOC..."
$word = New-Object -ComObject Word.Application
$word.Visible = $false
Get-ChildItem $Path -Recurse -Filter '*.doc' | ForEach-Object {
    $Stats.total++; $Stats.doc++
    try {
        $doc = $word.Documents.Open($_.FullName, $false, $true)
        $text = $doc.Content.Text
        $doc.Close()
        $m = [Regex]::Matches($text, $EmailPattern)
        if ($m.Count -gt 0) {
            $Results += [PSCustomObject]@{File=$_.Name; Folder=$_.Directory.Name; Tipo='DOC'; Emails=($m.Value | Select-Object -Unique) -join ', '}
        }
    } catch {}
}
$word.Quit()

# --- 4. XLSX ---
Write-Output "[4/5] Escaneando XLSX..."
Get-ChildItem $Path -Recurse -Filter '*.xlsx' | ForEach-Object {
    $Stats.total++; $Stats.xlsx++
    try {
        $zip = [System.IO.Compression.ZipFile]::OpenRead($_.FullName)
        $text = ""
        # Read shared strings
        $entry = $zip.GetEntry('xl/sharedStrings.xml')
        if ($entry) {
            $r = New-Object System.IO.StreamReader($entry.Open())
            $text += $r.ReadToEnd(); $r.Close()
        }
        # Read all worksheets
        $zip.Entries | Where-Object { $_.Name -like 'sheet*.xml' } | ForEach-Object {
            $r = New-Object System.IO.StreamReader($_.Open())
            $text += $r.ReadToEnd(); $r.Close()
        }
        $zip.Dispose()
        if ($text) {
            $text = [Regex]::Replace($text, '<[^>]+>', ' ')
            $text = [System.Web.HttpUtility]::HtmlDecode($text)
            $m = [Regex]::Matches($text, $EmailPattern)
            if ($m.Count -gt 0) {
                $Results += [PSCustomObject]@{File=$_.Name; Folder=$_.Directory.Name; Tipo='XLSX'; Emails=($m.Value | Select-Object -Unique) -join ', '}
            }
        }
    } catch {}
}

# --- 5. XLS (old binary) ---
Write-Output "[5/5] Escaneando XLS..."
$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false
Get-ChildItem $Path -Recurse -Filter '*.xls' | ForEach-Object {
    $Stats.total++; $Stats.xls++
    try {
        $wb = $excel.Workbooks.Open($_.FullName, $false, $true)
        $text = ""
        foreach ($ws in $wb.Worksheets) {
            $used = $ws.UsedRange
            if ($used) {
                $text += $used.Text + " "
            }
        }
        $wb.Close($false)
        $m = [Regex]::Matches($text, $EmailPattern)
        if ($m.Count -gt 0) {
            $Results += [PSCustomObject]@{File=$_.Name; Folder=$_.Directory.Name; Tipo='XLS'; Emails=($m.Value | Select-Object -Unique) -join ', '}
        }
    } catch {}
}
$excel.Quit()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null

# --- 6. PDF (raw binary search) ---
Write-Output "[6/5] Escaneando PDF..."
Get-ChildItem $Path -Recurse -Filter '*.pdf' | ForEach-Object {
    $Stats.total++; $Stats.pdf++
    try {
        $fs = [System.IO.File]::OpenRead($_.FullName)
        $buf = New-Object byte[] (512*1024)
        $read = $fs.Read($buf, 0, $buf.Length)
        $fs.Close()
        if ([Array]::IndexOf($buf, [byte]0x40) -ge 0) {
            $text = [Text.Encoding]::ASCII.GetString($buf, 0, $read)
            $m = [Regex]::Matches($text, $EmailPattern)
            if ($m.Count -gt 0) {
                $Results += [PSCustomObject]@{File=$_.Name; Folder=$_.Directory.Name; Tipo='PDF'; Emails=($m.Value | Select-Object -Unique) -join ', '}
            }
        }
    } catch {}
}

# --- REPORTE ---
Write-Output ""
Write-Output "=== RESULTADOS ==="
Write-Output "Archivos escaneados: $($Stats.total) (TXT:$($Stats.txt) DOCX:$($Stats.docx) DOC:$($Stats.doc) XLSX:$($Stats.xlsx) XLS:$($Stats.xls) PDF:$($Stats.pdf))"
Write-Output ""

if ($Results.Count -eq 0) {
    Write-Output "NO se encontraron emails."
    exit
}

# Build email -> file mapping
$AllEmails = @{}
$Results | ForEach-Object {
    $entry = $_
    $entry.Emails -split ', ' | ForEach-Object {
        $email = $_.Trim().ToLower()
        if (-not $AllEmails.ContainsKey($email)) { $AllEmails[$email] = @() }
        $AllEmails[$email] += $entry.File
    }
}

# Filter out false positives (2-letter TLDs, single-char local parts)
$ValidEmails = $AllEmails.GetEnumerator() | Where-Object {
    $parts = $_ -split '@'
    $parts[0].Length -ge 2 -and $parts[1] -notmatch '^[a-z]{1,2}\.[a-z]{2}$'
}

Write-Output "=== EMAILS UNICOS ENCONTRADOS ==="
$ValidEmails | Sort-Object Name | ForEach-Object {
    Write-Output ""
    Write-Output "  $($_.Name)"
    Write-Output "  $('-' * [Math]::Min($_.Name.Length, 60))"
    $_.Value | Sort-Object -Unique | ForEach-Object { Write-Output "    -> $_" }
}

Write-Output ""
Write-Output "=== RESUMEN ==="
$ValidEmails | Sort-Object Name | ForEach-Object {
    Write-Output ("  {0,-50} -> {1,3} archivos" -f $_.Name, ($_.Value | Sort-Object -Unique).Count)
}

# Show false positives separately
$FakeEmails = $AllEmails.GetEnumerator() | Where-Object { $_ -notin $ValidEmails }
if ($FakeEmails) {
    Write-Output ""
    Write-Output "=== FALSOS POSITIVOS (ruido binario) ==="
    $FakeEmails | Sort-Object Name | ForEach-Object {
        Write-Output ("  {0,-20} -> {1}" -f $_.Name, (($_.Value | Sort-Object -Unique).Count))
    }
}

Write-Output ""
Write-Output "($($Results.Count) archivos con emails, $($ValidEmails.Count) correos reales unicos)"
