import json
import os
from pathlib import Path

try:
    CARPETA = Path(__file__).resolve().parent
except NameError:
    CARPETA = Path(os.getcwd())

F_SORTEO = CARPETA / "sorteo_fantasy.json"
F_RES = CARPETA / "resultados_fantasy.json"


# ─────────────── DATOS ───────────────
def cargar_sorteo():
    if not F_SORTEO.exists():
        raise SystemExit("❌ No encuentro sorteo_fantasy.json. Haz antes los 3 sorteos "
                         "y deja este script en la misma carpeta.")
    d = json.loads(F_SORTEO.read_text(encoding="utf-8"))
    if not d.get("calendario"):
        raise SystemExit("❌ El sorteo del calendario no está completo.")
    return d


def cargar_resultados():
    if F_RES.exists():
        lista = json.loads(F_RES.read_text(encoding="utf-8"))
        return {(j, l, v): [pl, pv] for j, l, v, pl, pv in lista}
    return {}


def guardar_resultados(res):
    lista = [[j, l, v, pl, pv] for (j, l, v), (pl, pv) in sorted(res.items())]
    F_RES.write_text(json.dumps(lista, ensure_ascii=False, indent=1), encoding="utf-8")


SORTEO = cargar_sorteo()
CAL = SORTEO["calendario"]
RES = cargar_resultados()


def partidos_de(j):
    fila = CAL[j - 1]
    return [(k, l, v) for k in "AB" for l, v in fila[k]["partidos"]]


def jugados(j):
    return sum(1 for _, l, v in partidos_de(j) if (j, l, v) in RES)


def jornada_sugerida():
    for j in range(1, 11):
        if jugados(j) < 6:
            return j
    return 10


# ─────────────── ENTRADA ───────────────
def pedir_num(texto, actual=None):
    """Devuelve float, o None si se deja en blanco (no cambiar / saltar)."""
    marca = f" [actual: {actual:g}]" if actual is not None else ""
    while True:
        t = input(f"      {texto}{marca}: ").strip().replace(",", ".")
        if t == "":
            return None
        try:
            x = float(t)
            if x < 0:
                print("      ⚠ No puede ser negativo.")
                continue
            return x
        except ValueError:
            print("      ⚠ Escribe un número (ejemplo: 71.5 o 71,5).")


def cabecera(j):
    print(f"\n══════ JORNADA {j} · Liga J{CAL[j - 1]['liga']} · "
          f"{'IDA' if j <= 5 else 'VUELTA'} ══════")


def ver_jornada(j):
    cabecera(j)
    for k, l, v in partidos_de(j):
        r = RES.get((j, l, v))
        marcador = f"{r[0]:g} - {r[1]:g}" if r else "pendiente"
        print(f"  Grupo {k} │ {l:>8} vs {v:<8} │ {marcador}")


def introducir(j):
    cabecera(j)
    print("  Enter vacío = saltar ese partido (o mantener el valor actual).\n")
    for k, l, v in partidos_de(j):
        r = RES.get((j, l, v))
        print(f"  Grupo {k} │ {l} (local) vs {v} (visitante)")
        pl = pedir_num(f"Puntos de {l}", r[0] if r else None)
        if pl is None and not r:
            print("      → saltado\n")
            continue
        pv = pedir_num(f"Puntos de {v}", r[1] if r else None)
        pl = pl if pl is not None else r[0]
        pv = pv if pv is not None else (r[1] if r else None)
        if pv is None:
            print("      → saltado (faltaba un valor)\n")
            continue
        RES[(j, l, v)] = [pl, pv]
        guardar_resultados(RES)  # se guarda tras cada partido
        print(f"      ✅ Guardado: {l} {pl:g} - {pv:g} {v}\n")
    print(f"  Jornada {j}: {jugados(j)}/6 partidos con resultado.")


def borrar(j):
    ver_jornada(j)
    t = input("\n  Nº de partido a borrar (1-6, Enter para cancelar): ").strip()
    if not t.isdigit() or not 1 <= int(t) <= 6:
        print("  Cancelado.")
        return
    k, l, v = partidos_de(j)[int(t) - 1]
    if (j, l, v) in RES:
        del RES[(j, l, v)]
        guardar_resultados(RES)
        print(f"  🗑 Borrado {l} vs {v}.")
    else:
        print("  Ese partido no tenía resultado.")


def pedir_jornada(defecto):
    while True:
        t = input(f"  Jornada (1-10) [Enter = {defecto}]: ").strip()
        if t == "":
            return defecto
        if t.isdigit() and 1 <= int(t) <= 10:
            return int(t)
        print("  ⚠ Escribe un número del 1 al 10.")


def estado_general():
    print("\n  ESTADO DE LAS JORNADAS")
    for j in range(1, 11):
        n = jugados(j)
        icono = "✅" if n == 6 else ("🟡" if n else "⬜")
        print(f"   {icono} J{j:<2} (Liga J{CAL[j - 1]['liga']}): {n}/6")


# ─────────────── MENÚ ───────────────
def main():
    print("\n🏆 FANTASY CHAMPIONS · ACTUALIZAR RESULTADOS")
    while True:
        estado_general()
        print("\n  1) Introducir / corregir resultados de una jornada")
        print("  2) Ver resultados de una jornada")
        print("  3) Borrar un resultado")
        print("  0) Salir")
        op = input("\n  Elige opción: ").strip()
        if op == "1":
            introducir(pedir_jornada(jornada_sugerida()))
        elif op == "2":
            ver_jornada(pedir_jornada(jornada_sugerida()))
        elif op == "3":
            borrar(pedir_jornada(jornada_sugerida()))
        elif op == "0":
            print("\n  ¡Hasta la próxima jornada! 👋\n")
            break
        else:
            print("  ⚠ Opción no válida.")


if __name__ == "__main__":
    main()