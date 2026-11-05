# Agendamento do ponto

Agenda o script de ponto (em `C:\Users\victor\ferramentas\ponto\`) no **Agendador de Tarefas do Windows**,
para a batida acontecer sozinha nos horarios definidos.

## Uso

1. Copie `agendar_ponto.ps1` para `C:\Users\victor\ferramentas\ponto\`.
2. Abra o PowerShell nessa pasta e rode (troque `ponto.py` pelo nome real do seu script):

```powershell
powershell -ExecutionPolicy Bypass -File .\agendar_ponto.ps1 `
  -Script .\ponto.py -Horarios 08:00,12:00,13:00,17:00
```

Opcoes:

| Parametro          | Padrao           | Descricao                                             |
|--------------------|------------------|-------------------------------------------------------|
| `-Horarios`        | (obrigatorio)    | Lista `HH:mm` das batidas                             |
| `-Dias`            | Seg a Sex        | Ex.: `-Dias Monday,Wednesday,Friday`                  |
| `-VariacaoMinutos` | 0                | Atraso aleatorio de 0 a N minutos em cada batida      |
| `-Listar`          |                  | Mostra proxima/ultima execucao e codigo de retorno    |
| `-Remover`         |                  | Apaga todos os agendamentos de ponto                  |

Rodar de novo com outros horarios atualiza as tarefas (as antigas com outro horario continuam;
use `-Remover` antes se quiser trocar tudo).

## Como funciona

- Cria uma tarefa por horario na pasta `\Ponto\` do Agendador de Tarefas.
- `.py` roda com `py` (ou `python`); `.ps1`, `.bat` e `.exe` tambem funcionam.
- **Acorda o PC** da suspensao para bater, e se o PC estava desligado no horario,
  roda assim que ele ligar (`StartWhenAvailable`).
- Roda na sua sessao (precisa estar logado), entao scripts que abrem navegador funcionam.
- Toda execucao e registrada em `ponto.log`, na pasta do script.

## Requisitos do script

O script precisa rodar sem interacao (sem `input()` pedindo senha, etc.).
Se ele pede credenciais, leia de variavel de ambiente ou de um arquivo de config local.
