$env:AWS_ACCESS_KEY_ID = "test"
$env:AWS_SECRET_ACCESS_KEY = "test"
$env:AWS_DEFAULT_REGION = "ap-northeast-2"

$Endpoint = "http://localhost:4566"
$Bucket = "deploy-test"
$SeedDir = Join-Path $PSScriptRoot "seed"

aws s3api create-bucket --bucket $Bucket --region $env:AWS_DEFAULT_REGION --endpoint-url $Endpoint 2>$null
if (-not $?) { Write-Host "Bucket create skipped (may already exist)" }

aws s3 sync $SeedDir "s3://$Bucket" --delete --endpoint-url $Endpoint --checksum-algorithm SHA256
Write-Host "Seeded $Bucket from $SeedDir"
