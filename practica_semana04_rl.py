"""Q-Learning y comparación de Reward Shaping en un Gridworld 4x4."""

import random
from typing import Callable, List, Optional, Tuple

import numpy as np


class EntornoGridworldEstocastico:
    """Entorno 4x4 con acción deseada y desviaciones laterales."""

    def __init__(
        self, reward_shaping: bool = False, semilla: Optional[int] = None
    ) -> None:
        self.filas = 4
        self.columnas = 4
        self.n_estados = 16
        self.n_acciones = 4  # 0: izquierda, 1: abajo, 2: derecha, 3: arriba
        self.agujeros = {5, 7, 11, 12}
        self.meta = 15
        self.estado_actual = 0
        self.reward_shaping = reward_shaping
        self.rng = random.Random(semilla)
        self._terminado = False

    def reset(self) -> int:
        self.estado_actual = 0
        self._terminado = False
        return self.estado_actual

    def step(self, accion: int) -> Tuple[int, float, bool]:
        if not 0 <= accion < self.n_acciones:
            raise ValueError(f"acción fuera de rango: {accion}")
        if self._terminado:
            raise RuntimeError("El episodio terminó; llama a reset() antes de step()")

        # La acción deseada ocurre en un tercio de los pasos; los otros dos
        # tercios se reparten equitativamente entre sus dos vecinos laterales.
        if self.rng.random() >= 1.0 / 3.0:
            accion = (accion + self.rng.choice((-1, 1))) % self.n_acciones

        fila, columna = divmod(self.estado_actual, self.columnas)
        if accion == 0:
            columna = max(0, columna - 1)
        elif accion == 1:
            fila = min(self.filas - 1, fila + 1)
        elif accion == 2:
            columna = min(self.columnas - 1, columna + 1)
        else:
            fila = max(0, fila - 1)

        nuevo_estado = fila * self.columnas + columna
        self.estado_actual = nuevo_estado
        self._terminado = nuevo_estado in self.agujeros or nuevo_estado == self.meta

        if nuevo_estado in self.agujeros:
            recompensa = -1.0 if self.reward_shaping else 0.0
        elif nuevo_estado == self.meta:
            recompensa = 1.0
        else:
            recompensa = -0.01 if self.reward_shaping else 0.0

        return nuevo_estado, recompensa, self._terminado


def entrenar_q_learning(
    env: EntornoGridworldEstocastico,
    episodios: int = 2000,
    alpha: float = 0.8,
    gamma: float = 0.95,
    *,
    epsilon_inicial: float = 1.0,
    epsilon_minimo: float = 0.01,
    decaimiento_epsilon: float = 0.995,
    max_pasos_por_episodio: int = 1000,
    semilla: Optional[int] = None,
    al_finalizar_episodio: Optional[Callable[[bool], None]] = None,
) -> np.ndarray:
    """Entrena Q-Learning y devuelve la tabla Q, manteniendo la API de la plantilla."""
    if episodios <= 0:
        raise ValueError("episodios debe ser mayor que cero")
    if max_pasos_por_episodio <= 0:
        raise ValueError("max_pasos_por_episodio debe ser mayor que cero")
    if not 0 < alpha <= 1:
        raise ValueError("alpha debe estar en el intervalo (0, 1]")
    if not 0 <= gamma <= 1:
        raise ValueError("gamma debe estar en el intervalo [0, 1]")
    if not 0 <= epsilon_minimo <= epsilon_inicial <= 1:
        raise ValueError("se requiere 0 <= epsilon_minimo <= epsilon_inicial <= 1")
    if not 0 < decaimiento_epsilon <= 1:
        raise ValueError("decaimiento_epsilon debe estar en el intervalo (0, 1]")
    if semilla is not None:
        env.rng.seed(semilla)

    q_table = np.zeros((env.n_estados, env.n_acciones), dtype=float)
    epsilon = epsilon_inicial

    for _ in range(episodios):
        estado = env.reset()
        terminado = False
        exito = False

        for _ in range(max_pasos_por_episodio):
            if env.rng.random() < epsilon:
                accion = env.rng.randrange(env.n_acciones)
            else:
                accion = int(np.argmax(q_table[estado, :]))

            siguiente_estado, recompensa, terminado = env.step(accion)
            exito = terminado and siguiente_estado == env.meta

            # Los estados terminales no deben recibir valor futuro del bootstrap.
            objetivo_td = recompensa
            if not terminado:
                objetivo_td += gamma * float(np.max(q_table[siguiente_estado, :]))
            error_td = objetivo_td - q_table[estado, accion]
            q_table[estado, accion] += alpha * error_td

            estado = siguiente_estado
            if terminado:
                break

        if al_finalizar_episodio is not None:
            al_finalizar_episodio(exito)
        epsilon = max(epsilon_minimo, epsilon * decaimiento_epsilon)

    return q_table


def reportar_tasa_exito(exitos: List[bool], tamano_bloque: int = 100) -> None:
    """Imprime la tasa de éxito para bloques completos y parciales."""
    if tamano_bloque <= 0:
        raise ValueError("tamano_bloque debe ser mayor que cero")

    for inicio in range(0, len(exitos), tamano_bloque):
        bloque = exitos[inicio : inicio + tamano_bloque]
        tasa = sum(bloque) / len(bloque)
        fin = inicio + len(bloque)
        print(
            f"Episodios {inicio + 1:4d}-{fin:4d}: "
            f"{tasa:.1%} ({sum(bloque)}/{len(bloque)})"
        )


def ejecutar_experimento(
    reward_shaping: bool,
    *,
    episodios: int = 2000,
    tamano_bloque: int = 100,
    semilla: int = 42,
) -> np.ndarray:
    nombre = "Reward Shaping" if reward_shaping else "Entorno estándar"
    print(f"\n--- {nombre} ---")
    env = EntornoGridworldEstocastico(
        reward_shaping=reward_shaping, semilla=semilla
    )
    exitos: List[bool] = []
    q_table = entrenar_q_learning(
        env,
        episodios=episodios,
        semilla=semilla,
        al_finalizar_episodio=exitos.append,
    )
    reportar_tasa_exito(exitos, tamano_bloque)
    return q_table


def main() -> None:
    print("=== EVALUACIÓN EJERCICIO 2: Q-LEARNING Y REWARD SHAPING ===")
    q_estandar = ejecutar_experimento(reward_shaping=False)
    q_shaping = ejecutar_experimento(reward_shaping=True)
    print("\nTabla Q Entorno Estándar (Estado 0):", np.round(q_estandar[0, :], 3))
    print("Tabla Q Reward Shaping (Estado 0):", np.round(q_shaping[0, :], 3))


if __name__ == "__main__":
    main()
