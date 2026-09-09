# resume_download_xtts.ps1
$ErrorActionPreference = "Continue"
$target = "C:\Users\DELL\AppData\Local\tts\tts_models--multilingual--multi-dataset--xtts_v2\model.pth"
$url = "https://huggingface.co/coqui/XTTS-v2/resolve/main/model.pth"
$expectedSize = 1867929118

$dir = Split-Path $target
if (!(Test-Path $dir)) {
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
}

$attempt = 0
while ($true) {
    $attempt++
    if (Test-Path $target) {
        $currentSize = (Get-Item $target).Length
        $pct = [math]::Round(($currentSize / $expectedSize) * 100, 2)
        $mb = [math]::Round($currentSize / 1MB, 2)
        Write-Host "[$attempt] Progress: $mb MB / 1781.4 MB ($pct%)"
        if ($currentSize -ge $expectedSize) {
            Write-Host "SUCCESS: XTTS-v2 model.pth download complete!"
            break
        }
    } else {
        $currentSize = 0
        Write-Host "[$attempt] Starting download from byte 0..."
    }

    # Run curl with resume (-C -) and fast AWS CDN IP with auto-recovery on stalls
    & curl.exe -L -C - --resolve huggingface.co:443:143.204.106.71 --resolve us.aws.cdn.hf.co:443:52.221.162.66 --connect-timeout 10 --speed-limit 5000 --speed-time 15 -o $target $url
    
    Start-Sleep -Seconds 2
}
