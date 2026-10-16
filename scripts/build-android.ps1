$ErrorActionPreference = 'Stop'
$taskProjectRoot = Split-Path -Parent $PSScriptRoot
Push-Location -LiteralPath $taskProjectRoot
try {
    & node node_modules/@angular/cli/bin/ng.js build --configuration production
    if ($LASTEXITCODE -ne 0) { throw 'Angular build failed' }
    & node node_modules/@capacitor/cli/bin/capacitor sync android
    if ($LASTEXITCODE -ne 0) { throw 'Capacitor sync failed' }
    $taskSdkPath = if ($env:ANDROID_HOME) { $env:ANDROID_HOME } else { Join-Path $env:LOCALAPPDATA 'Android/Sdk' }
    if (!(Test-Path -LiteralPath $taskSdkPath)) { throw 'Android SDK was not found; set ANDROID_HOME' }
    Set-Content -LiteralPath 'android/local.properties' -Value ('sdk.dir=' + $taskSdkPath.Replace('\','/')) -Encoding ascii
    $taskJava = if ($env:JAVA_HOME) { Join-Path $env:JAVA_HOME 'bin/java.exe' } else { (Get-Command java).Source }
    Push-Location -LiteralPath 'android'
    try {
        $taskGradleArgs = @(':app:assembleDebug','--console=plain')
        if ($env:RB_MAVEN_MIRROR -eq '1') { $taskGradleArgs += @('--init-script','maven-mirror.init.gradle') }
        & $taskJava -classpath 'gradle/wrapper/gradle-wrapper.jar' org.gradle.wrapper.GradleWrapperMain @taskGradleArgs
        if ($LASTEXITCODE -ne 0) { throw 'Android build failed' }
    } finally { Pop-Location }
    New-Item -ItemType Directory -Path 'releases' -Force | Out-Null
    Copy-Item -LiteralPath 'android/app/build/outputs/apk/debug/app-debug.apk' -Destination 'releases/rafiq-baz-debug.apk'
    Write-Output 'Built releases/rafiq-baz-debug.apk (debug signing, design review only).'
} finally { Pop-Location }
