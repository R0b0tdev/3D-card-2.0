$ErrorActionPreference = 'Stop'
$viewerUrl = 'http://localhost:8765/'
$viewerFolder = $PSScriptRoot
$running = $false
try { $response = Invoke-WebRequest -Uri $viewerUrl -UseBasicParsing -TimeoutSec 2; $running = $response.StatusCode -eq 200 } catch {}
if (-not $running) {
    if ($viewerFolder.StartsWith('\\wsl.localhost\Ubuntu\')) {
        $linuxFolder = '/' + $viewerFolder.Substring('\\wsl.localhost\Ubuntu\'.Length).Replace('\','/')
    } elseif ($viewerFolder.StartsWith('\\wsl$\Ubuntu\')) {
        $linuxFolder = '/' + $viewerFolder.Substring('\\wsl$\Ubuntu\'.Length).Replace('\','/')
    } else {
        $linuxFolder = (wsl -d Ubuntu -- wslpath -a $viewerFolder).Trim()
    }
    Start-Process -FilePath 'wsl.exe' -ArgumentList @('-d','Ubuntu','--','python3','-m','http.server','8765','--bind','127.0.0.1','--directory',$linuxFolder) -WindowStyle Hidden
    for ($attempt=0; $attempt -lt 20; $attempt++) {
        Start-Sleep -Milliseconds 300
        try { $response = Invoke-WebRequest -Uri $viewerUrl -UseBasicParsing -TimeoutSec 1; if ($response.StatusCode -eq 200) { break } } catch {}
    }
}
Start-Process $viewerUrl

