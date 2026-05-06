# Verify MVP PowerShell Script
# Run from project root after docker compose up -d
# All checks must print OK

$BASE = "http://localhost:8000"
Write-Host "=== Kebos Deception MVP Verification ===" 

# 1. Backend health
Write-Host -NoNewline "1. Backend health... "
try {
    $response = Invoke-WebRequest -Uri "$BASE/health" -UseBasicParsing -ErrorAction Stop
    if ($response.StatusCode -eq 200) { Write-Host "OK" }
    else { Write-Host "FAIL (got $($response.StatusCode))" }
} catch { Write-Host "FAIL" }

# 2. Traps endpoint
Write-Host -NoNewline "2. Traps endpoint... "
try {
    $response = Invoke-WebRequest -Uri "$BASE/api/v1/deception/traps" -UseBasicParsing -ErrorAction Stop
    if ($response.StatusCode -eq 200) { Write-Host "OK" }
    else { Write-Host "FAIL (got $($response.StatusCode))" }
} catch { Write-Host "FAIL" }

# 3. Threats endpoint
Write-Host -NoNewline "3. Threats endpoint... "
try {
    $response = Invoke-WebRequest -Uri "$BASE/api/v1/threats/" -UseBasicParsing -ErrorAction Stop
    if ($response.StatusCode -eq 200) { Write-Host "OK" }
    else { Write-Host "FAIL (got $($response.StatusCode))" }
} catch { Write-Host "FAIL" }

# 4. SSH trap port open
Write-Host -NoNewline "4. SSH trap port open... "
$tcp = New-Object System.Net.Sockets.TcpClient
$sshResult = $tcp.ConnectAsync("localhost", 2222).Wait(3000)
if ($sshResult) { Write-Host "OK" } else { Write-Host "FAIL (start SSH trap first)" }
$tcp.Close()

# 5. HTTP trap port open
Write-Host -NoNewline "5. HTTP trap port open... "
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8080/" -UseBasicParsing -ErrorAction Stop
    if ($response.StatusCode -eq 200) { Write-Host "OK" }
    else { Write-Host "FAIL (got $($response.StatusCode))" }
} catch { Write-Host "FAIL" }

# 6. RDP trap port open
Write-Host -NoNewline "6. RDP trap port open... "
$tcp2 = New-Object System.Net.Sockets.TcpClient
$rdpResult = $tcp2.ConnectAsync("localhost", 3389).Wait(3000)
if ($rdpResult) { Write-Host "OK" } else { Write-Host "FAIL (start RDP trap first)" }
$tcp2.Close()

# 7. QMind health
Write-Host -NoNewline "7. QMind health... "
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8001/health" -UseBasicParsing -ErrorAction Stop
    if ($response.StatusCode -eq 200) { Write-Host "OK" }
    else { Write-Host "FAIL (got $($response.StatusCode))" }
} catch { Write-Host "FAIL" }

# 8. Frontend serving
Write-Host -NoNewline "8. Frontend serving... "
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5173/" -UseBasicParsing -ErrorAction Stop
    if ($response.StatusCode -eq 200) { Write-Host "OK" }
    else { Write-Host "FAIL" }
} catch { Write-Host "FAIL" }

Write-Host ""
Write-Host "Run simulate_attack.py after all OKs:"
Write-Host "  python simulate_attack.py --target localhost"
