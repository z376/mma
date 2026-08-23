<#
mma AI 详情编译脚本:编译 论文/AI工具使用详情.tex -> AI工具使用详情.pdf,
并复制到 支撑材料/ 压缩包目录。

要求:
- 已安装 xelatex(在 PATH)
- 论文/AI工具使用详情.tex 存在(从 AI工具使用详情-template.tex 复制并填写)

用法:
    powershell -File build_ai_detail.ps1                # 当前目录下 论文/AI工具使用详情.tex
    powershell -File build_ai_detail.ps1 -WorkSpace C:\path\to\workspace

兼容:Windows PowerShell 5.1 / PowerShell 7+ (pwsh)

退出码:
    0 = 编译成功
    1 = 编译失败 / 模板文件未找到
    2 = xelatex 未安装
#>

param(
    [string]$WorkSpace = "."
)

$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true

$paperDir = Join-Path $WorkSpace "论文"
$supportDir = Join-Path $WorkSpace "支撑材料"
$texFile = Join-Path $paperDir "AI工具使用详情.tex"
$templateFile = Join-Path $paperDir "AI工具使用详情-template.tex"
$pdfFile = Join-Path $paperDir "AI工具使用详情.pdf"
$destPDF = Join-Path $supportDir "AI工具使用详情.pdf"

# 检查 xelatex
$xelatex = Get-Command xelatex -ErrorAction SilentlyContinue
if (-not $xelatex) {
    Write-Host "[FAIL] xelatex 未安装或不在 PATH(需要 TeX Live 或 MiKTeX)" -ForegroundColor Red
    exit 2
}

# PowerShell 兼容
$psVer = $PSVersionTable.PSVersion
Write-Host "[PS] PowerShell: $psVer" -ForegroundColor Cyan

# 检查 tex 文件
if (-not (Test-Path $texFile)) {
    Write-Host "[FAIL] $texFile 不存在" -ForegroundColor Red
    if (Test-Path $templateFile) {
        Write-Host ""
        Write-Host "提示:从模板复制一份并填写:" -ForegroundColor Yellow
        Write-Host "  Copy-Item '$templateFile' '$texFile'" -ForegroundColor Yellow
        Write-Host "  然后用编辑器填写【】占位符"
    } else {
        Write-Host "模板文件 $templateFile 也不存在" -ForegroundColor Red
    }
    exit 1
}

# 编译
Write-Host ""
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host "编译 AI 工具使用详情(独立 PDF,放支撑材料)" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host "论文目录: $paperDir"
Write-Host "源文件:   $texFile"

Push-Location $paperDir
try {
    for ($i = 1; $i -le 2; $i++) {
        Write-Host "[Pass $i/2] xelatex AI工具使用详情.tex ..."
        # 不接 Out-Null,直接丢弃标准输出,避免 PS 5.1 LASTEXITCODE 异常
        $output = & xelatex -interaction=nonstopmode "AI工具使用详情.tex" 2>&1
        $null = $output
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[FAIL] 编译失败(Pass $i),exit=$LASTEXITCODE" -ForegroundColor Red
            Write-Host "查看日志: $paperDir\AI工具使用详情.log" -ForegroundColor Red
            exit 1
        }
    }
}
finally {
    Pop-Location
}

# 验证 PDF
if (-not (Test-Path $pdfFile)) {
    Write-Host "[FAIL] 编译后未生成 $pdfFile" -ForegroundColor Red
    exit 1
}

# 复制到 支撑材料/
if (-not (Test-Path $supportDir)) {
    New-Item -ItemType Directory -Path $supportDir -Force | Out-Null
}
Copy-Item -Path $pdfFile -Destination $destPDF -Force
$size = (Get-Item $destPDF).Length

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "[OK] AI 详情 PDF 已生成" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host "论文/AI工具使用详情.pdf:    $pdfFile"
Write-Host "支撑材料/AI工具使用详情.pdf: $destPDF ($([math]::Round($size/1KB, 1)) KB)" -ForegroundColor Green
Write-Host ""
Write-Host "[TIP] 压缩支撑材料时记得保留 支撑材料/AI工具使用详情.pdf(2026 规定第 4 条必交)" -ForegroundColor Green
exit 0
