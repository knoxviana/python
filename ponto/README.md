# Batida de ponto agendada

Faz o `ponto.py registrar` rodar sozinho nos horários definidos, via **Agendador de Tarefas do Windows**.

## Instalação

1. Copie `agendar_ponto.ps1` e `ponto_agendado.py` para `C:\Users\victor\ferramentas\ponto\`
   (mesma pasta do `ponto.py`).
2. Teste uma vez à mão: `python ponto.py testar` (abre o modal e cancela).
3. No PowerShell, nessa pasta:

```powershell
powershell -ExecutionPolicy Bypass -File .\agendar_ponto.ps1 -Horarios 08:00,12:00,13:00,17:00
```

| Parâmetro          | Padrão                | Descrição                                          |
|--------------------|-----------------------|----------------------------------------------------|
| `-Horarios`        | (obrigatório)         | Lista `HH:mm` das batidas                          |
| `-Dias`            | Seg a Sex             | Ex.: `-Dias Monday,Wednesday,Friday`               |
| `-VariacaoMinutos` | 0                     | Atraso aleatório de 0 a N minutos                  |
| `-Script`          | `ponto_agendado.py`   | Outro script a rodar                               |
| `-Listar`          |                       | Próxima/última execução e código de retorno        |
| `-Remover`         |                       | Apaga todos os agendamentos                        |

Para trocar os horários: `-Remover` e agende de novo.

## O que acontece em cada horário

`ponto_agendado.py` faz **uma** tentativa, e antes confere:

- **Dia pulado** (`pular_datas` no `ponto.json`): não faz nada.
- **Tela bloqueada ou PC sem uso** há mais de `ociosidade_max_min` (15): não bate; mostra aviso
  "NÃO feita, bata manualmente". Assim nunca registra ponto com você longe do PC.
- **Você já bateu** nos últimos `tolerancia_min` (20) minutos: ignora (sem duplicar).
- Senão registra e mostra um aviso que some em 20 s. Se falhar, mostra o erro e **não tenta de novo**.

Tudo fica registrado em `ponto.log`.

```json
{
  "jornada": "08:00",
  "agendamento": {
    "ociosidade_max_min": 15,
    "tolerancia_min": 20,
    "pular_datas": ["2026-12-24", "2026-12-28..2027-01-02"]
  }
}
```

## Limitações

- Precisa estar logado com o Chrome aberto no Batida Online e a sessão do Ahgora válida.
- Se o PC estiver dormindo/desligado no horário, a batida é pulada (não acorda nem bate atrasado).
- Batidas no relógio físico não aparecem na página, então a checagem de duplicidade não as vê.
