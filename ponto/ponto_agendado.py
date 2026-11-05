"""Batida automática: é o que o Agendador de Tarefas chama (ver agendar_ponto.ps1).

Fica na mesma pasta do ponto.py e usa as funções dele. Antes de registrar, confere:
  1. se hoje não está em "pular_datas" (férias, feriado, folga);
  2. se a tela não está bloqueada e você mexeu no PC nos últimos minutos
     (não bate ponto com você longe do computador);
  3. se você já não bateu manualmente há pouco (evita marcação duplicada).
Faz uma única tentativa, igual ao ponto.py: se falhar, avisa na tela para você
bater à mão, e nunca tenta de novo sozinho.

Configuração opcional em ponto.json:
  "agendamento": {
    "ociosidade_max_min": 15,
    "tolerancia_min": 20,
    "pular_datas": ["2026-12-24", "2026-12-28..2027-01-02"]
  }
"""
import ctypes
import os
import subprocess
import sys
from datetime import date, datetime, timedelta

import ponto

PADRAO = {"ociosidade_max_min": 15, "tolerancia_min": 20, "pular_datas": []}


def cfg_agendamento():
    return {**PADRAO, **(ponto.config().get("agendamento") or {})}


def dia_pulado(hoje, pular_datas):
    for item in pular_datas:
        ini, _, fim = item.partition("..")
        if date.fromisoformat(ini) <= hoje <= date.fromisoformat(fim or ini):
            return True
    return False


def batida_recente(horas, agora, tolerancia_min):
    """Primeira batida de hoje feita nos últimos `tolerancia_min` minutos, se houver."""
    for h in horas:
        t = datetime.combine(agora.date(), datetime.strptime(h, "%H:%M").time())
        if timedelta(0) <= agora - t <= timedelta(minutes=tolerancia_min):
            return h
    return None


def tela_bloqueada():
    # LogonUI.exe só roda com a tela de bloqueio/login aberta
    r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq LogonUI.exe", "/NH"],
                       capture_output=True, text=True)
    return "logonui.exe" in r.stdout.lower()


def ocioso_min():
    class LASTINPUTINFO(ctypes.Structure):
        _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]

    lii = LASTINPUTINFO()
    lii.cbSize = ctypes.sizeof(lii)
    if not ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii)):
        return 0.0
    ctypes.windll.kernel32.GetTickCount.restype = ctypes.c_uint32
    return ((ctypes.windll.kernel32.GetTickCount() - lii.dwTime) & 0xFFFFFFFF) / 60000


def avisar(msg, erro=False):
    """Janela por cima de tudo. Sucesso some sozinho em 20 s; erro fica até você fechar.
    Roda em processo separado para não segurar a tarefa agendada."""
    icone = 48 if erro else 64  # 48 = alerta, 64 = informação; +4096 = sempre por cima
    espera = 0 if erro else 20
    cmd = (f"(New-Object -ComObject WScript.Shell).Popup($env:PONTO_MSG, {espera}, "
           f"'Ponto', {icone + 4096}) | Out-Null")
    flags = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
    env = {**os.environ, "PONTO_MSG": msg}
    args = ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", cmd]
    try:
        subprocess.Popen(args, env=env, creationflags=flags | 0x01000000)  # + BREAKAWAY_FROM_JOB
    except OSError:
        subprocess.Popen(args, env=env, creationflags=flags)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    agora = datetime.now()
    c = cfg_agendamento()

    if dia_pulado(agora.date(), c["pular_datas"]):
        print("Hoje está em pular_datas: nada feito.")
        return 0

    if tela_bloqueada():
        msg = f"Batida das {agora:%H:%M} NÃO feita: a tela estava bloqueada. Bata manualmente."
        print(msg)
        avisar(msg, erro=True)
        return 0

    ocioso = ocioso_min()
    if ocioso > c["ociosidade_max_min"]:
        msg = (f"Batida das {agora:%H:%M} NÃO feita: o PC estava sem uso havia "
               f"{ocioso:.0f} min. Bata manualmente se estiver trabalhando.")
        print(msg)
        avisar(msg, erro=True)
        return 0

    try:
        jan = ponto.janela_batida()
        horas = ponto.registros(ponto.recarregar(jan))
        h = batida_recente(horas, agora, c["tolerancia_min"])
        if h:
            print(f"Você já bateu às {h}: batida agendada das {agora:%H:%M} ignorada.")
            return 0
        res = ponto.bater(confirmar=True)
    except ponto.Falha as e:
        msg = f"NÃO registrado: {e}"
        print(msg)
        avisar(msg, erro=True)
        return 1
    except Exception as e:  # erro inesperado: não arrisca repetir
        msg = f"NÃO registrado (erro inesperado: {e}). Confira no site e bata manualmente."
        print(msg)
        avisar(msg, erro=True)
        return 1

    print(res)
    avisar(res)
    return 0


if __name__ == "__main__":
    sys.exit(main())
