<#
mma 编译脚本:一键编译论文.tex(纸质版)+ 电子版.tex(电子版),各 2 次。
要求:已安装 xelatex(在 PATH),并在 论文/ 目录运行。

用法:
    pwsh -File build.ps1                # 编译当前目录下 论文/ 里的两份
    pwsh -File build.ps1 -WorkSpace C:\path\to\workspace  # 指定工作区

退出码:
    0 = 编译成功
    1 = 编译失败
    2 = xelatex 未安装
#>

param(
    [string]$WorkSpace = "."
)

$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true

$paperDir = Join-Path $WorkSpace "论文"
if (-not (Test-Path $paperDir)) {
    Write-Host "❌ 论文/ 目录不存在:$paperDir" -ForegroundColor Red
    exit 1
}

# 检查 xelatex
$xelatex = Get-Command xelatex -ErrorAction SilentlyContinue
if (-not $xelatex) {
    Write-Host "❌ xelatex 未安装或不在 PATH(需要 TeX Live 或 MiKTeX)" -ForegroundColor Red
    exit 2
}

Write-Host "📂 论文目录:$paperDir" -ForegroundColor Cyan
Write-Host "🔨 xelatex: $($xelatex.Source)" -ForegroundColor Cyan
Write-Host ""

# 编译 论文.tex(纸质版)
Write-Host "=" * 60
Write-Host "📄 编译 论文.tex(纸质版,含承诺书+编号页)" -ForegroundColor Yellow
Write-Host "=" * 60
Push-Location $paperDir
try {
    for ($i = 1; $i -le 2; $i++) {
        Write-Host "[Pass $i/2] xelatex 论文.tex ..."
        & xelatex -interaction=nonstopmode "论文.tex" 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ 论文.tex 编译失败(Pass $i)" -ForegroundColor Red
            exit 1
        }
    }
}
finally {
    Pop-Location
}

# 编译 电子版.tex(电子版)
Write-Host ""
Write-Host "=" * 60
Write-Host "📄 编译 电子版.tex(电子版,跳过承诺书+编号页)" -ForegroundColor Yellow
Write-Host "=" * 60
Push-Location $paperDir
try {
    for ($i = 1; $i -le 2; $i++) {
        Write-Host "[Pass $i/2] xelatex 电子版.tex ..."
        & xelatex -interaction=nonstopmode "电子版.tex" 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ 电子版.tex 编译失败(Pass $i)" -ForegroundColor Red
            exit 1
        }
    }
}
finally {
    Pop-Location
}

# 验证 PDF 存在
$paperPDF = Join-Path $paperDir "论文.pdf"
$elecPDF = Join-Path $paperDir "电子版.pdf"

Write-Host ""
Write-Host "=" * 60
Write-Host "✅ 编译完成" -ForegroundColor Green
Write-Host "=" * 60

if (Test-Path $paperPDF) {
    $size = (Get-Item $paperPDF).Length
    Write-Host "📄 论文.pdf :$paperPDF ($([math]::Round($size/1KB, 1)) KB)" -ForegroundColor Green
} else {
    Write-Host "❌ 论文.pdf 未生成" -ForegroundColor Red
    exit 1
}

if (Test-Path $elecPDF) {
    $size = (Get-Item $elecPDF).Length
    Write-Host "📄 电子版.pdf:$elecPDF ($([math]::Round($size/1KB, 1)) KB)" -ForegroundColor Green
} else {
    Write-Host "❌ 电子版.pdf 未生成" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🎉 两份 PDF 已就绪,可直接提交" -ForegroundColor Green
exit 0
