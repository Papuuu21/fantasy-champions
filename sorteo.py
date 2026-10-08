import os
import random
import sys
import time

# ─────────────────────────────────────────────
#  SORTEO DE GRUPOS · FANTASY CHAMPIONS
# ─────────────────────────────────────────────

PARTICIPANTES = ["Palop", "Fale", "Lope", "Tony", "Ruso", "Kero",
                 "Coquina", "Papu", "Kike", "Gonzo", "Puche", "Armada"]

rng = random.SystemRandom()  # aleatoriedad del sistema operativo (no predecible)

# Colores ANSI
AMARILLO = "\033[93m"
AZUL = "\033[96m"
VERDE = "\033[92m"
ROJO = "\033[91m"
NEGRITA = "\033[1m"
RESET = "\033[0m"

os.system("")  # activa los colores ANSI en Windows


def limpiar():
    os.system("cls" if os.name == "nt" else "clear")


def escribir(texto, delay=0.03):
    for c in texto:
        sys.stdout.write(c)
        sys.stdout.flush()
        time.sleep(delay)
    print()


def suspense(puntos=3, pausa=0.6):
    for _ in range(puntos):
        time.sleep(pausa)
        sys.stdout.write(".")
        sys.stdout.flush()
    time.sleep(pausa)
    print()


def ruleta(opciones, final, pasos=28, ancho=14):
    """Animación de bombo: va mostrando bolas y se frena en la elegida."""
    for i in range(pasos):
        if i == pasos - 1:
            valor = final
        else:
            valor = rng.choice(opciones)
        sys.stdout.write(f"\r   🎱  {AMARILLO}{valor:^{ancho}}{RESET}")
        sys.stdout.flush()
        time.sleep(0.04 + i * 0.008)  # cada vez más lento
    print()


def mostrar_tabla(grupos, nuevo=None):
    print(f"{NEGRITA}{'GRUPO A':^28}{'GRUPO B':^28}{RESET}")
    print("═" * 28 + "  " + "═" * 26)
    for i in range(6):
        fila = ""
        for g in ("A", "B"):
            if i < len(grupos[g]):
                nombre = grupos[g][i]
                texto = f"{i + 1}. {nombre}".ljust(26)
                if nombre == nuevo:
                    texto = f"{VERDE}{NEGRITA}{texto}{RESET}"
            else:
                texto = f"{i + 1}. ···".ljust(26)
            fila += texto + "  "
        print(fila)
    print()


def pausa(auto):
    """Devuelve True si se activa el modo automático."""
    if auto:
        time.sleep(1.5)
        return True
    r = input(f"{AZUL}   ▶ ENTER para continuar (o 'a' para modo automático)... {RESET}")
    return r.strip().lower() == "a"


def main():
    limpiar()
    print(f"{AMARILLO}{NEGRITA}")
    print("  ╔══════════════════════════════════════════════╗")
    print("  ║      🏆  FANTASY CHAMPIONS LEAGUE  🏆        ║")
    print("  ║            SORTEO DE GRUPOS                  ║")
    print("  ╚══════════════════════════════════════════════╝")
    print(RESET)
    escribir("  Buenas noches y bienvenidos al sorteo de la fase de grupos.")
    escribir("  12 participantes, 2 grupos de 6. Se clasifican los 4 primeros.")
    print()
    escribir("  Participantes en el bombo:")
    for i in range(0, 12, 4):
        print("   " + "  ·  ".join(PARTICIPANTES[i:i + 4]))
    print()
    input(f"{AZUL}  ▶ Pulsa ENTER para empezar el sorteo... {RESET}")

    bombo_nombres = PARTICIPANTES.copy()
    bombo_grupos = ["A"] * 6 + ["B"] * 6
    grupos = {"A": [], "B": []}
    auto = False

    for turno in range(1, 13):
        limpiar()
        print(f"{NEGRITA}  🏆 SORTEO FANTASY CHAMPIONS · Bola {turno}/12{RESET}\n")
        mostrar_tabla(grupos)

        # ── BOLA DE PARTICIPANTE ──
        print(f"  {NEGRITA}BOMBO DE PARTICIPANTES{RESET} ({len(bombo_nombres)} bolas)")
        auto = pausa(auto) or auto
        print("\n  Removiendo el bombo...")
        elegido = rng.choice(bombo_nombres)
        bombo_nombres.remove(elegido)
        ruleta(bombo_nombres + [elegido], elegido)
        sys.stdout.write("  Se abre la bola")
        suspense()
        print(f"\n  👉 {AMARILLO}{NEGRITA}{elegido.upper()}{RESET}\n")
        time.sleep(1)

        # ── BOLA DE GRUPO ──
        print(f"  {NEGRITA}BOMBO DE GRUPOS{RESET} (quedan {bombo_grupos.count('A')} bolas A "
              f"y {bombo_grupos.count('B')} bolas B)")
        auto = pausa(auto) or auto
        print("\n  Removiendo el bombo...")
        grupo = rng.choice(bombo_grupos)
        bombo_grupos.remove(grupo)
        ruleta(["A", "B"], grupo, pasos=22, ancho=6)
        sys.stdout.write("  Se abre la bola")
        suspense()
        print(f"\n  👉 {NEGRITA}{elegido}{RESET} jugará en el {VERDE}{NEGRITA}GRUPO {grupo}{RESET}\n")
        grupos[grupo].append(elegido)
        time.sleep(1.2)

        print()
        mostrar_tabla(grupos, nuevo=elegido)
        if turno < 12:
            auto = pausa(auto) or auto

    # ── RESUMEN FINAL ──
    limpiar()
    print(f"{AMARILLO}{NEGRITA}")
    print("  ╔══════════════════════════════════════════════╗")
    print("  ║         ✅ SORTEO FINALIZADO ✅              ║")
    print("  ╚══════════════════════════════════════════════╝")
    print(RESET)
    mostrar_tabla(grupos)
    print(f"  {VERDE}Pasan a la siguiente fase los 4 primeros de cada grupo.{RESET}")
    print(f"  {NEGRITA}¡Suerte a todos!{RESET}\n")

    return grupos


if __name__ == "__main__":
    grupos_sorteados = main()