<#
mma 编译脚本:一键编译论文.tex(纸质版)+ 电子版.tex(电子版)+ AI工具使用详情.tex(支撑材料),各 2 次。
要求:已安装 xelatex(在 PATH)。

用法:
    powershell -File build.ps1                # 编译当前目录下 论文/ 里的三份
    powershell -File build.ps1 -WorkSpace C:\path\to\workspace  # 指定工作区

兼容:Windows PowerShell 5.1 / PowerShell 7+ (pwsh)

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
    Write-Host "[FAIL] 论文/ 目录不存在:$paperDir" -ForegroundColor Red
    exit 1
}

# 检查 xelatex
$xelatex = Get-Command xelatex -ErrorAction SilentlyContinue
if (-not $xelatex) {
    Write-Host "[FAIL] xelatex 未安装或不在 PATH(需要 TeX Live 或 MiKTeX)" -ForegroundColor Red
    exit 2
}

$psVer = $PSVersionTable.PSVersion
Write-Host "论文目录: $paperDir" -ForegroundColor Cyan
Write-Host "xelatex:   $($xelatex.Source)" -ForegroundColor Cyan
Write-Host "PowerShell: $psVer" -ForegroundColor Cyan
Write-Host ""

# 编译 论文.tex(纸质版)
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host "编译 论文.tex(纸质版,含承诺书+编号页)" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Yellow
Push-Location $paperDir
try {
    for ($i = 1; $i -le 2; $i++) {
        Write-Host "[Pass $i/2] xelatex 论文.tex ..."
        $output = & xelatex -interaction=nonstopmode "论文.tex" 2>&1
        $null = $output
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[FAIL] 论文.tex 编译失败(Pass $i),exit=$LASTEXITCODE" -ForegroundColor Red
            exit 1
        }
    }
}
finally {
    Pop-Location
}

# 编译 电子版.tex(电子版)
Write-Host ""
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host "编译 电子版.tex(电子版,跳过承诺书+编号页)" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Yellow
Push-Location $paperDir
try {
    for ($i = 1; $i -le 2; $i++) {
        Write-Host "[Pass $i/2] xelatex 电子版.tex ..."
        $output = & xelatex -interaction=nonstopmode "电子版.tex" 2>&1
        $null = $output
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[FAIL] 电子版.tex 编译失败(Pass $i),exit=$LASTEXITCODE" -ForegroundColor Red
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
Write-Host "============================================================" -ForegroundColor Green
Write-Host "[OK] 论文 PDF 编译完成" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green

if (Test-Path $paperPDF) {
    $size = (Get-Item $paperPDF).Length
    Write-Host "论文.pdf:  $paperPDF ($([math]::Round($size/1KB, 1)) KB)" -ForegroundColor Green
} else {
    Write-Host "[FAIL] 论文.pdf 未生成" -ForegroundColor Red
    exit 1
}

if (Test-Path $elecPDF) {
    $size = (Get-Item $elecPDF).Length
    Write-Host "电子版.pdf: $elecPDF ($([math]::Round($size/1KB, 1)) KB)" -ForegroundColor Green
} else {
    Write-Host "[FAIL] 电子版.pdf 未生成" -ForegroundColor Red
    exit 1
}

# 编译 AI 工具使用详情(2026 规定第 4 条必交)
$aiTexFile = Join-Path $paperDir "AI工具使用详情.tex"
$aiPdfDest = Join-Path $WorkSpace "支撑材料/AI工具使用详情.pdf"
if (Test-Path $aiTexFile) {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Yellow
    Write-Host "编译 AI 工具使用详情(独立 PDF,放支撑材料)" -ForegroundColor Yellow
    Write-Host "============================================================" -ForegroundColor Yellow
    Push-Location $paperDir
    try {
        for ($i = 1; $i -le 2; $i++) {
            Write-Host "[Pass $i/2] xelatex AI工具使用详情.tex ..."
            $output = & xelatex -interaction=nonstopmode "AI工具使用详情.tex" 2>&1
            $null = $output
            if ($LASTEXITCODE -ne 0) {
                Write-Host "[FAIL] AI 详情编译失败(Pass $i),exit=$LASTEXITCODE" -ForegroundColor Red
                exit 1
            }
        }
    }
    finally {
        Pop-Location
    }
    $aiPdfSrc = Join-Path $paperDir "AI工具使用详情.pdf"
    if (Test-Path $aiPdfSrc) {
        $supportDir = Join-Path $WorkSpace "支撑材料"
        if (-not (Test-Path $supportDir)) {
            New-Item -ItemType Directory -Path $supportDir -Force | Out-Null
        }
        Copy-Item -Path $aiPdfSrc -Destination $aiPdfDest -Force
        $size = (Get-Item $aiPdfDest).Length
        Write-Host "支撑材料/AI工具使用详情.pdf: $aiPdfDest ($([math]::Round($size/1KB, 1)) KB)" -ForegroundColor Green

        # 避免冗余:删除 论文/AI工具使用详情.pdf(只保留 支撑材料/ 里的版本)
        try {
            [System.IO.File]::Delete($aiPdfSrc)
            Write-Host "       已删除 论文/AI工具使用详情.pdf(冗余,仅留 支撑材料/ 版本)" -ForegroundColor DarkGray
        } catch {
            Write-Host "       [WARN] 删除 论文/AI工具使用详情.pdf 失败:$($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host ""
    Write-Host "[SKIP] AI 工具使用详情:跳过(论文/AI工具使用详情.tex 不存在)" -ForegroundColor DarkGray
    Write-Host "       提示:从 论文/AI工具使用详情-template.tex 复制并填写后,再跑 build.ps1" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "[DONE] 所有 PDF 已就绪,可直接提交" -ForegroundColor Green
exit 0
