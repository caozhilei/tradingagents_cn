# ============================================================================
# 一键打包可执行应用程序脚本
# ============================================================================
# 功能：
# 1. 构建前端
# 2. 同步代码到便携版目录
# 3. 设置嵌入式Python（如需要）
# 4. 创建便携版ZIP包
# 5. 创建NSIS安装程序（可选）
# ============================================================================

param(
    [string]$Version = "",
    [switch]$SkipFrontend = $false,
    [switch]$SkipPortable = $false,
    [switch]$SkipInstaller = $false,
    [switch]$SkipEmbeddedPython = $false,
    [string]$BackendPort = "8000",
    [string]$MongoPort = "27017",
    [string]$RedisPort = "6379",
    [string]$NginxPort = "80",
    [string]$PythonVersion = "3.10.11"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "  TradingAgents-CN 可执行应用程序打包工具" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# 步骤 1: 读取版本号
# ============================================================================

if (-not $Version) {
    $versionFile = Join-Path $root "VERSION"
    if (Test-Path $versionFile) {
        $Version = (Get-Content $versionFile -Raw).Trim()
        Write-Host "📌 版本号: $Version (从 VERSION 文件读取)" -ForegroundColor Green
    } else {
        $Version = "1.0.0-preview"
        Write-Host "⚠️  未找到 VERSION 文件，使用默认版本: $Version" -ForegroundColor Yellow
    }
} else {
    Write-Host "📌 版本号: $Version (命令行指定)" -ForegroundColor Green
}

Write-Host ""

# ============================================================================
# 步骤 2: 构建前端（除非跳过）
# ============================================================================

if (-not $SkipFrontend) {
    Write-Host "[1/5] 构建前端..." -ForegroundColor Yellow
    Write-Host ""

    $frontendDir = Join-Path $root "frontend"
    if (Test-Path $frontendDir) {
        try {
            Write-Host "  安装前端依赖..." -ForegroundColor Gray
            $installProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "cd /d `"$frontendDir`" && yarn install --frozen-lockfile" -Wait -PassThru -NoNewWindow

            if ($installProcess.ExitCode -ne 0) {
                Write-Host "  ⚠️  yarn install 失败，退出码: $($installProcess.ExitCode)" -ForegroundColor Yellow
            } else {
                Write-Host "  ✅ 依赖安装完成" -ForegroundColor Green
            }

            Write-Host "  构建前端（这可能需要几分钟）..." -ForegroundColor Gray
            $buildProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "cd /d `"$frontendDir`" && yarn vite build" -Wait -PassThru -NoNewWindow

            if ($buildProcess.ExitCode -ne 0) {
                Write-Host "  ❌ 前端构建失败，退出码: $($buildProcess.ExitCode)" -ForegroundColor Red
                exit 1
            } else {
                Write-Host "  ✅ 前端构建完成" -ForegroundColor Green
            }
        } catch {
            Write-Host "  ❌ 前端构建出错: $_" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "  ⚠️  前端目录不存在: $frontendDir" -ForegroundColor Yellow
    }
    Write-Host ""
} else {
    Write-Host "[1/5] 跳过前端构建" -ForegroundColor Gray
    Write-Host ""
}

# ============================================================================
# 步骤 3: 创建便携版包（除非跳过）
# ============================================================================

if (-not $SkipPortable) {
    Write-Host "[2/5] 创建便携版包..." -ForegroundColor Yellow
    Write-Host ""

    $buildPortableScript = Join-Path $root "scripts\deployment\build_portable_package.ps1"
    if (Test-Path $buildPortableScript) {
        try {
            $skipEmbeddedPythonParam = if ($SkipEmbeddedPython) { "-SkipEmbeddedPython" } else { "" }
            
            & powershell -ExecutionPolicy Bypass -File $buildPortableScript `
                -Version $Version `
                -SkipSync:$false `
                $skipEmbeddedPythonParam `
                -SkipPackage:$false `
                -PythonVersion $PythonVersion

            if ($LASTEXITCODE -ne 0) {
                Write-Host "  ❌ 便携版打包失败，退出码: $LASTEXITCODE" -ForegroundColor Red
                exit 1
            } else {
                Write-Host "  ✅ 便携版打包完成" -ForegroundColor Green
            }
        } catch {
            Write-Host "  ❌ 便携版打包出错: $_" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "  ❌ 找不到打包脚本: $buildPortableScript" -ForegroundColor Red
        exit 1
    }
    Write-Host ""
} else {
    Write-Host "[2/5] 跳过便携版打包" -ForegroundColor Gray
    Write-Host ""
}

# ============================================================================
# 步骤 4: 创建NSIS安装程序（除非跳过）
# ============================================================================

if (-not $SkipInstaller) {
    Write-Host "[3/5] 创建NSIS安装程序..." -ForegroundColor Yellow
    Write-Host ""

    # 查找NSIS编译器
    $nsisPaths = @(
        "C:\Program Files (x86)\NSIS\makensis.exe",
        "C:\Program Files\NSIS\makensis.exe",
        "${env:ProgramFiles(x86)}\NSIS\makensis.exe",
        "${env:ProgramFiles}\NSIS\makensis.exe"
    )

    $nsisExe = $null
    foreach ($path in $nsisPaths) {
        if (Test-Path $path) {
            $nsisExe = $path
            break
        }
    }

    if (-not $nsisExe) {
        Write-Host "  ⚠️  未找到NSIS编译器，跳过安装程序创建" -ForegroundColor Yellow
        Write-Host "  提示: 请从 https://nsis.sourceforge.io/Download 下载并安装NSIS" -ForegroundColor Gray
        Write-Host ""
    } else {
        Write-Host "  找到NSIS编译器: $nsisExe" -ForegroundColor Green

        # 查找便携版ZIP包
        $packagesDir = Join-Path $root "release\packages"
        $zipPattern = "TradingAgentsCN-Portable-$Version-*.zip"
        $zipFiles = Get-ChildItem -Path $packagesDir -Filter $zipPattern -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending

        if ($zipFiles.Count -eq 0) {
            Write-Host "  ❌ 未找到便携版ZIP包: $packagesDir\$zipPattern" -ForegroundColor Red
            Write-Host "  请先运行便携版打包步骤" -ForegroundColor Yellow
            exit 1
        }

        $latestZip = $zipFiles[0]
        Write-Host "  使用便携版包: $($latestZip.Name)" -ForegroundColor Cyan

        # 准备NSIS脚本参数
        $nsisScript = Join-Path $root "scripts\windows-installer\nsis\installer.nsi"
        if (-not (Test-Path $nsisScript)) {
            Write-Host "  ❌ 找不到NSIS脚本: $nsisScript" -ForegroundColor Red
            exit 1
        }

        # 创建临时NSIS脚本（带参数）
        $tempNsisScript = Join-Path $env:TEMP "installer_$([guid]::NewGuid()).nsi"
        $nsisContent = Get-Content $nsisScript -Raw -Encoding UTF8
        
        # 替换变量
        $nsisContent = $nsisContent -replace '!define PRODUCT_VERSION ".*"', "!define PRODUCT_VERSION `"$Version`""
        $nsisContent = $nsisContent -replace '!define BACKEND_PORT ".*"', "!define BACKEND_PORT `"$BackendPort`""
        $nsisContent = $nsisContent -replace '!define MONGO_PORT ".*"', "!define MONGO_PORT `"$MongoPort`""
        $nsisContent = $nsisContent -replace '!define REDIS_PORT ".*"', "!define REDIS_PORT `"$RedisPort`""
        $nsisContent = $nsisContent -replace '!define NGINX_PORT ".*"', "!define NGINX_PORT `"$NginxPort`""
        $nsisContent = $nsisContent -replace '!define PACKAGE_ZIP ".*"', "!define PACKAGE_ZIP `"$($latestZip.FullName)`""
        $nsisContent = $nsisContent -replace '!define OUTPUT_DIR ".*"', "!define OUTPUT_DIR `"$packagesDir`""

        [System.IO.File]::WriteAllText($tempNsisScript, $nsisContent, [System.Text.Encoding]::UTF8)

        try {
            Write-Host "  编译NSIS安装程序（这可能需要几分钟）..." -ForegroundColor Gray
            $nsisProcess = Start-Process -FilePath $nsisExe -ArgumentList "`"$tempNsisScript`"" -Wait -PassThru -NoNewWindow

            if ($nsisProcess.ExitCode -ne 0) {
                Write-Host "  ❌ NSIS编译失败，退出码: $($nsisProcess.ExitCode)" -ForegroundColor Red
                Remove-Item $tempNsisScript -ErrorAction SilentlyContinue
                exit 1
            } else {
                Write-Host "  ✅ NSIS安装程序创建完成" -ForegroundColor Green
                
                $installerExe = Join-Path $packagesDir "TradingAgentsCNSetup-$Version.exe"
                if (Test-Path $installerExe) {
                    $fileInfo = Get-Item $installerExe
                    $fileSizeMB = [math]::Round($fileInfo.Length / 1MB, 2)
                    Write-Host "  安装程序: $($fileInfo.Name) ($fileSizeMB MB)" -ForegroundColor Cyan
                }
            }
        } catch {
            Write-Host "  ❌ NSIS编译出错: $_" -ForegroundColor Red
            Remove-Item $tempNsisScript -ErrorAction SilentlyContinue
            exit 1
        } finally {
            Remove-Item $tempNsisScript -ErrorAction SilentlyContinue
        }
    }
    Write-Host ""
} else {
    Write-Host "[3/5] 跳过安装程序创建" -ForegroundColor Gray
    Write-Host ""
}

# ============================================================================
# 步骤 5: 显示结果
# ============================================================================

Write-Host "[4/5] 打包完成！" -ForegroundColor Green
Write-Host ""

$packagesDir = Join-Path $root "release\packages"
if (Test-Path $packagesDir) {
    Write-Host "📦 输出目录: $packagesDir" -ForegroundColor Cyan
    Write-Host ""

    # 显示便携版ZIP
    $zipFiles = Get-ChildItem -Path $packagesDir -Filter "TradingAgentsCN-Portable-*.zip" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
    if ($zipFiles.Count -gt 0) {
        Write-Host "便携版ZIP包:" -ForegroundColor White
        foreach ($zip in $zipFiles[0..([Math]::Min(3, $zipFiles.Count - 1))]) {
            $sizeMB = [math]::Round($zip.Length / 1MB, 2)
            Write-Host "  • $($zip.Name) ($sizeMB MB)" -ForegroundColor Gray
        }
        Write-Host ""
    }

    # 显示安装程序
    $installerFiles = Get-ChildItem -Path $packagesDir -Filter "TradingAgentsCNSetup-*.exe" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
    if ($installerFiles.Count -gt 0) {
        Write-Host "安装程序:" -ForegroundColor White
        foreach ($exe in $installerFiles[0..([Math]::Min(3, $installerFiles.Count - 1))]) {
            $sizeMB = [math]::Round($exe.Length / 1MB, 2)
            Write-Host "  • $($exe.Name) ($sizeMB MB)" -ForegroundColor Gray
        }
        Write-Host ""
    }
}

Write-Host "============================================================================" -ForegroundColor Green
Write-Host "  打包完成！" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "下一步:" -ForegroundColor White
Write-Host "  1. 测试便携版ZIP包（解压后运行 start_all.ps1）" -ForegroundColor Gray
Write-Host "  2. 测试安装程序（在另一台电脑上安装）" -ForegroundColor Gray
Write-Host "  3. 分发安装程序给其他用户" -ForegroundColor Gray
Write-Host ""

