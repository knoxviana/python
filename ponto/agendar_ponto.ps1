<#
.SYNOPSIS
  Agenda (ou remove) a execucao automatica do script de ponto no Agendador de Tarefas do Windows.

.EXAMPLE
  # Agenda 4 batidas de segunda a sexta
  .\agendar_ponto.ps1 -Script "C:\Users\victor\ferramentas\ponto\ponto.py" -Horarios 08:00,12:00,13:00,17:00

.EXAMPLE
  # Com ate 3 minutos de variacao aleatoria em cada batida
  .\agendar_ponto.ps1 -Script "C:\Users\victor\ferramentas\ponto\ponto.py" -Horarios 08:00,17:00 -VariacaoMinutos 3

.EXAMPLE
  # Lista as batidas agendadas
  .\agendar_ponto.ps1 -Listar

.EXAMPLE
  # Remove todas as batidas agendadas
  .\agendar_ponto.ps1 -Remover
#>
[CmdletBinding(DefaultParameterSetName = 'Agendar')]
param(
    [Parameter(ParameterSetName = 'Agendar', Mandatory)]
    [string]$Script,

    [Parameter(ParameterSetName = 'Agendar', Mandatory)]
    [string[]]$Horarios,

    [Parameter(ParameterSetName = 'Agendar')]
    [ValidateSet('Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday')]
    [string[]]$Dias = @('Monday','Tuesday','Wednesday','Thursday','Friday'),

    [Parameter(ParameterSetName = 'Agendar')]
    [ValidateRange(0, 30)]
    [int]$VariacaoMinutos = 0,

    [Parameter(ParameterSetName = 'Remover', Mandatory)]
    [switch]$Remover,

    [Parameter(ParameterSetName = 'Listar', Mandatory)]
    [switch]$Listar
)

$ErrorActionPreference = 'Stop'
$Pasta = '\Ponto\'

if ($Listar) {
    Get-ScheduledTask -TaskPath $Pasta -ErrorAction SilentlyContinue |
        ForEach-Object {
            $info = $_ | Get-ScheduledTaskInfo
            [pscustomobject]@{
                Tarefa        = $_.TaskName
                Proxima       = $info.NextRunTime
                Ultima        = $info.LastRunTime
                UltimoRetorno = $info.LastTaskResult
            }
        } | Format-Table -AutoSize
    return
}

if ($Remover) {
    Get-ScheduledTask -TaskPath $Pasta -ErrorAction SilentlyContinue |
        Unregister-ScheduledTask -Confirm:$false
    Write-Host 'Agendamentos de ponto removidos.'
    return
}

$Script = (Resolve-Path $Script).Path
$PastaScript = Split-Path $Script -Parent
$Log = Join-Path $PastaScript 'ponto.log'

# Monta o comando conforme o tipo de arquivo
switch ([IO.Path]::GetExtension($Script).ToLower()) {
    '.py' {
        $py = (Get-Command py -ErrorAction SilentlyContinue).Source
        if (-not $py) { $py = (Get-Command python -ErrorAction Stop).Source }
        $comando = "`"$py`" `"$Script`""
    }
    '.ps1' { $comando = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$Script`"" }
    default { $comando = "`"$Script`"" }
}

# cmd /c para registrar data/hora e toda a saida (stdout + stderr) em ponto.log
$argumentos = "/c echo ===== %DATE% %TIME% >> `"$Log`" & $comando >> `"$Log`" 2>&1"
$acao = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument $argumentos -WorkingDirectory $PastaScript

$config = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -WakeToRun `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10) `
    -MultipleInstances IgnoreNew

# Roda na sessao do usuario logado (necessario se o script abre navegador/janela)
$usuario = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive

foreach ($h in $Horarios) {
    $hora = [datetime]::ParseExact($h, 'HH:mm', $null)
    $gatilho = New-ScheduledTaskTrigger -Weekly -DaysOfWeek $Dias -At $hora
    if ($VariacaoMinutos -gt 0) {
        $gatilho.RandomDelay = [System.Xml.XmlConvert]::ToString((New-TimeSpan -Minutes $VariacaoMinutos))
    }
    $nome = 'Batida ' + $hora.ToString('HH\hmm')
    Register-ScheduledTask -TaskPath $Pasta -TaskName $nome -Action $acao -Trigger $gatilho `
        -Settings $config -Principal $usuario -Force | Out-Null
    Write-Host "Agendado: $nome ($($Dias -join ', '))"
}

Write-Host ""
Write-Host "Log de execucao: $Log"
Write-Host "Conferir: .\agendar_ponto.ps1 -Listar   |   Remover: .\agendar_ponto.ps1 -Remover"
