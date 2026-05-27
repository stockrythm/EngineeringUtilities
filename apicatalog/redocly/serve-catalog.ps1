param(
    [int]   $Port      = 8080,
    [switch]$NoBrowser = $false
)

$Root = $PSScriptRoot

$mime = @{
    ".html" = "text/html; charset=utf-8"
    ".css"  = "text/css; charset=utf-8"
    ".js"   = "application/javascript; charset=utf-8"
    ".json" = "application/json; charset=utf-8"
    ".yaml" = "application/yaml; charset=utf-8"
    ".yml"  = "application/yaml; charset=utf-8"
    ".svg"  = "image/svg+xml"
    ".ico"  = "image/x-icon"
    ".txt"  = "text/plain; charset=utf-8"
}

$url      = "http://localhost:$Port/"
$listener = [System.Net.HttpListener]::new()
$listener.Prefixes.Add($url)

try {
    $listener.Start()
} catch {
    Write-Host "Could not bind to port $Port - is something already running there?" -ForegroundColor Red
    Write-Host "Try: .\serve-catalog.ps1 -Port 9000" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "  API Catalog Portal" -ForegroundColor Cyan
Write-Host "  Serving: $Root" -ForegroundColor DarkGray
Write-Host "  URL:     $url" -ForegroundColor Green
Write-Host "  Stop:    Ctrl+C" -ForegroundColor DarkGray
Write-Host ""

if (-not $NoBrowser) {
    Start-Process $url
}

try {
    while ($listener.IsListening) {
        $ctx = $listener.GetContext()
        $req = $ctx.Request
        $res = $ctx.Response

        $rawPath = $req.Url.LocalPath.TrimStart("/")
        if ($rawPath -eq "" -or $rawPath -eq "/") {
            $rawPath = "index.html"
        }
        $filePath = Join-Path $Root $rawPath

        if (Test-Path $filePath -PathType Leaf) {
            $ext         = [IO.Path]::GetExtension($filePath)
            $contentType = if ($mime.ContainsKey($ext)) { $mime[$ext] } else { "application/octet-stream" }
            $bytes       = [IO.File]::ReadAllBytes($filePath)

            $res.StatusCode          = 200
            $res.ContentType         = $contentType
            $res.ContentLength64     = $bytes.Length

            $res.Headers.Add("Access-Control-Allow-Origin", "*")
            $res.Headers.Add("Access-Control-Allow-Methods", "GET, OPTIONS")
            $res.Headers.Add("Access-Control-Allow-Headers", "Content-Type")
            $res.Headers.Add("Cache-Control", "no-cache")

            $res.OutputStream.Write($bytes, 0, $bytes.Length)
        } else {
            $body    = [Text.Encoding]::UTF8.GetBytes("404 Not Found: $rawPath")
            $res.StatusCode      = 404
            $res.ContentType     = "text/plain"
            $res.ContentLength64 = $body.Length
            $res.OutputStream.Write($body, 0, $body.Length)
        }

        $res.OutputStream.Close()
    }
} finally {
    $listener.Stop()
    Write-Host "Server stopped." -ForegroundColor DarkGray
}
