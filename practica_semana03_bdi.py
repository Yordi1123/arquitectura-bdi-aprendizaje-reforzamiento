"""Demostración de agente BDI para la práctica de laboratorio."""

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional


MITIGAR_INTRUSION_SEGURIDAD = "MITIGAR_INTRUSION_SEGURIDAD"
RESTAURAR_SERVICIO_CACHE = "RESTAURAR_SERVICIO_CACHE"
PREVENIR_CAIDA_OOM = "PREVENIR_CAIDA_OOM"
ESTABILIZAR_RENDIMIENTO_SLA = "ESTABILIZAR_RENDIMIENTO_SLA"

PLAN_AUTOESCALADO = "Runbook_Autoescalado_Horizontal"
PLAN_DEGRADACION = "Runbook_Degradacion_Elegante_CircuitBreaker"


@dataclass
class TelemetriaCluster:
    ciclo: int
    cpu_pct: float
    latencia_ms: float
    alerta_siem: bool
    cuota_agotada: bool = False


@dataclass
class Deseo:
    nombre: str
    prioridad: int


@dataclass
class PlanBDI:
    nombre: str
    intencion_meta: str
    precondicion: Callable[[Dict[str, Any]], bool]
    cuerpo_acciones: List[str]


def crear_biblioteca_planes() -> List[PlanBDI]:
    """Construye los runbooks requeridos con precondiciones explícitas."""
    return [
        PlanBDI(
            nombre=PLAN_AUTOESCALADO,
            intencion_meta=ESTABILIZAR_RENDIMIENTO_SLA,
            precondicion=lambda creencias: not creencias["cuota_cloud_agotada"],
            cuerpo_acciones=[
                "APROVISIONAR_NODO_REPLICA_K8S",
                "REBALANCEAR_TRAFICO_INGRESS",
            ],
        ),
        PlanBDI(
            nombre=PLAN_DEGRADACION,
            intencion_meta=ESTABILIZAR_RENDIMIENTO_SLA,
            precondicion=lambda creencias: creencias["cuota_cloud_agotada"],
            cuerpo_acciones=[
                "ACTIVAR_CIRCUIT_BREAKER_RECOMENDACIONES",
                "HABILITAR_RESPUESTA_ESTATICA_CDN",
            ],
        ),
    ]


BIBLIOTECA_PLANES = crear_biblioteca_planes()


class AgenteBDI_Estudiante:
    def __init__(
        self,
        umbral_latencia_cache_ms: Optional[float] = None,
        umbral_latencia_sla_ms: Optional[float] = None,
    ) -> None:
        for nombre, umbral in (
            ("umbral_latencia_cache_ms", umbral_latencia_cache_ms),
            ("umbral_latencia_sla_ms", umbral_latencia_sla_ms),
        ):
            if umbral is not None and umbral < 0:
                raise ValueError(f"{nombre} debe ser un valor no negativo")

        self.umbral_latencia_cache_ms = umbral_latencia_cache_ms
        self.umbral_latencia_sla_ms = umbral_latencia_sla_ms
        self.creencias: Dict[str, Any] = {
            "historial_cpu": [],
            "anomalia_fuga_memoria": False,
            "bajo_ataque": False,
            "cuota_cloud_agotada": False,
            "servicio_cache_degradado": False,
            "estabilizar_sla": False,
            "plan_fallido": None,
        }
        self.intencion_actual: Optional[Deseo] = None
        self.plan_activo: Optional[PlanBDI] = None
        self.cola_acciones: List[str] = []

    def brf(self, p: TelemetriaCluster) -> None:
        """Actualiza las creencias a partir de la telemetría del ciclo."""
        historial: List[float] = self.creencias["historial_cpu"]
        historial.append(p.cpu_pct)
        del historial[:-3]

        # Cada uno de los dos incrementos debe superar 15 puntos porcentuales.
        anomalia = (
            len(historial) == 3
            and historial[0] < historial[1] < historial[2]
            and historial[1] - historial[0] > 15.0
            and historial[2] - historial[1] > 15.0
        )
        self.creencias["anomalia_fuga_memoria"] = anomalia
        self.creencias["bajo_ataque"] = p.alerta_siem
        self.creencias["cuota_cloud_agotada"] = p.cuota_agotada

        # Sin umbrales proporcionados por la práctica, las señales de latencia
        # solo se calculan cuando el usuario configura sus límites.
        if self.umbral_latencia_cache_ms is not None:
            self.creencias["servicio_cache_degradado"] = (
                p.latencia_ms >= self.umbral_latencia_cache_ms
            )
        if self.umbral_latencia_sla_ms is not None:
            self.creencias["estabilizar_sla"] = (
                p.latencia_ms >= self.umbral_latencia_sla_ms
            )

        self._activar_fallback_si_cuota_agotada()

    def options(self) -> Dict[str, Deseo]:
        """Genera deseos activos en función de las creencias disponibles."""
        opciones: Dict[str, Deseo] = {}
        condiciones = (
            (
                MITIGAR_INTRUSION_SEGURIDAD,
                100,
                self.creencias["bajo_ataque"],
            ),
            (
                RESTAURAR_SERVICIO_CACHE,
                80,
                self.creencias["servicio_cache_degradado"],
            ),
            (
                PREVENIR_CAIDA_OOM,
                75,
                self.creencias["anomalia_fuga_memoria"],
            ),
            (
                ESTABILIZAR_RENDIMIENTO_SLA,
                60,
                self.creencias["estabilizar_sla"],
            ),
        )
        for nombre, prioridad, activo in condiciones:
            if activo:
                opciones[nombre] = Deseo(nombre, prioridad)
        return opciones

    def filter(self, opciones: Dict[str, Deseo]) -> Optional[Deseo]:
        """Elige el deseo activo de mayor prioridad."""
        if not opciones:
            return None
        return max(opciones.values(), key=lambda deseo: deseo.prioridad)

    def seleccionar_plan_fallback(
        self, intencion: Deseo, biblioteca: List[PlanBDI]
    ) -> Optional[PlanBDI]:
        """Selecciona el primer plan aplicable que no haya fallado."""
        plan_fallido = self.creencias["plan_fallido"]
        for plan in biblioteca:
            if (
                plan.intencion_meta == intencion.nombre
                and plan.nombre != plan_fallido
                and plan.precondicion(self.creencias)
            ):
                return plan
        return None

    def _activar_fallback_si_cuota_agotada(self) -> None:
        if not self.creencias["cuota_cloud_agotada"]:
            return

        plan_principal_activo = (
            self.plan_activo is not None
            and self.plan_activo.nombre == PLAN_AUTOESCALADO
        )
        intencion_sla_activa = (
            self.intencion_actual is not None
            and self.intencion_actual.nombre == ESTABILIZAR_RENDIMIENTO_SLA
        )
        if plan_principal_activo or intencion_sla_activa:
            self.creencias["plan_fallido"] = PLAN_AUTOESCALADO

        if not intencion_sla_activa:
            return

        plan_alternativo = self.seleccionar_plan_fallback(
            self.intencion_actual, BIBLIOTECA_PLANES
        )
        if plan_alternativo is not None:
            # Solo se reemplaza el plan; la intención SLA se conserva.
            self.plan_activo = plan_alternativo
            self.cola_acciones = list(plan_alternativo.cuerpo_acciones)


def main() -> None:
    print("=== EVALUACIÓN EJERCICIO 1: AGENTE BDI ===")
    agente = AgenteBDI_Estudiante()
    for ciclo, cpu in enumerate((40.0, 58.0, 75.0), start=1):
        agente.brf(
            TelemetriaCluster(
                ciclo=ciclo,
                cpu_pct=cpu,
                latencia_ms=0.0,
                alerta_siem=False,
            )
        )

    print("Historial CPU:", agente.creencias["historial_cpu"])
    print(
        "Anomalía de fuga antes del 80%:",
        agente.creencias["anomalia_fuga_memoria"],
    )

    # Estos indicadores permiten demostrar la jerarquía sin inventar límites
    # de latencia que no aparecen en el enunciado.
    agente.creencias["bajo_ataque"] = True
    agente.creencias["servicio_cache_degradado"] = True
    agente.creencias["estabilizar_sla"] = True
    deseos = agente.options()
    print(
        "Deseos por prioridad:",
        [(d.nombre, d.prioridad) for d in deseos.values()],
    )
    print("Intención seleccionada:", agente.filter(deseos))

    agente.intencion_actual = Deseo(ESTABILIZAR_RENDIMIENTO_SLA, 60)
    agente.plan_activo = BIBLIOTECA_PLANES[0]
    agente.brf(
        TelemetriaCluster(
            ciclo=4,
            cpu_pct=92.0,
            latencia_ms=0.0,
            alerta_siem=False,
            cuota_agotada=True,
        )
    )
    print("Plan fallido:", agente.creencias["plan_fallido"])
    print("Plan de fallback:", agente.plan_activo.nombre if agente.plan_activo else None)
    print("Intención preservada:", agente.intencion_actual)
    print("Acciones en cola:", agente.cola_acciones)


if __name__ == "__main__":
    main()
