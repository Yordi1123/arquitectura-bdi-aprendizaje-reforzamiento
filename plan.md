# Plan de implementación: Práctica 4 — Arquitectura BDI y aprendizaje por refuerzo

**Fecha**: 2026-10-14 | **Especificación**: [practica4.md](./practica4.md)

## Resumen

La práctica pide dos programas Python independientes: un agente deliberativo BDI para supervisar un clúster y un agente Q-Learning para un Gridworld estocástico. El plan conserva esa separación, completa los puntos TODO de las plantillas, hace explícitos los casos de fallback y compara el aprendizaje con y sin Reward Shaping.

Se mapearon siete requisitos (REQ-001 a REQ-007). La regla de CPU sigue la aclaración del usuario: las tres lecturas deben ser estrictamente crecientes y **cada incremento consecutivo debe superar 15 puntos porcentuales**. La práctica no fija los umbrales de latencia ni una señal directa de degradación de caché; se dejan como parámetros de diseño, sin inventar un valor obligatorio.

## Contexto técnico

- **Lenguaje/versión**: Python 3; la versión mínima no está especificada.
- **Dependencias**: biblioteca estándar (`dataclasses`, `typing`, `random`) y NumPy para la tabla Q.
- **Persistencia**: no aplica; estado en memoria durante cada ejecución.
- **Ejecución objetivo**: dos scripts ejecutables por separado desde la raíz del repositorio.
- **Restricciones**: nombres de archivo exactos indicados en la práctica, comentarios breves que justifiquen decisiones y ejecución sin errores sintácticos.
- **Evaluación**: cumplimiento de la rúbrica de 20 puntos; reporte de tasas de éxito por bloques de episodios para comparar ambos esquemas de recompensa.

## Verificación de principios

- Mantener los ejercicios independientes: **Cumple**; cada algoritmo y su punto de entrada vivirán en su propio archivo.
- Preservar las especificaciones y la rúbrica: **Cumple**; se implementan las ecuaciones, prioridades, reglas de transición y recompensas solicitadas.
- No inventar requisitos cuantitativos ausentes: **Cumple con salvedad**; los umbrales de latencia se parametrizan y quedan sujetos a confirmación.
- Constitución del proyecto: no se encontró un archivo de constitución; no se aplican principios adicionales.

## Guías aplicadas

No se identificaron guías de transformación pertinentes: el trabajo es una implementación académica nueva, no una migración entre tecnologías.

## Fases de implementación

### Fase 1: Preparación

#### Paso 1.1: Crear los puntos de entrada separados
- **Requisitos**: REQ-001
- **Entradas de diseño**: plantilla Python y nombres de archivo de `practica4.md`.
- **Descripción**: crear `practica_semana03_bdi.py` y `practica_semana04_rl.py`, conservar las responsabilidades separadas y preparar un punto de entrada en cada archivo para ejecutar la demostración del ejercicio correspondiente.

### Fase 2: Agente BDI (Semana 03)

#### Paso 2.1: Implementar revisión de creencias e inferencia de CPU
- **Requisitos**: REQ-002
- **Entradas de diseño**: regla deductiva aclarada por el usuario y clase `TelemetriaCluster`.
- **Descripción**: actualizar las creencias con cada lectura, conservar como máximo las últimas tres lecturas y derivar `anomalia_fuga_memoria` solo cuando haya tres valores estrictamente crecientes y ambos incrementos consecutivos sean mayores que 15 puntos porcentuales. No esperar a que CPU llegue al 80%. Recalcular la creencia a partir de la ventana actual y no activar inferencia con menos de tres valores.

#### Paso 2.2: Generar deseos y seleccionar la intención por prioridad
- **Requisitos**: REQ-003
- **Entradas de diseño**: señales disponibles en `TelemetriaCluster` y jerarquía de prioridades de la práctica.
- **Descripción**: implementar `options()` para generar deseos según creencias y `filter()` para elegir el de mayor prioridad. Mantener el orden fijo: intrusión (100), restaurar caché (80), prevenir OOM (75), estabilizar SLA (60). `alerta_siem` sustenta la señal de intrusión y la creencia de anomalía sustenta el deseo de prevenir OOM. La activación de caché/SLA se apoyará en latencia configurable, pues no se proporciona umbral en la guía.

#### Paso 2.3: Seleccionar planes y conmutar al fallback sin perder intención
- **Requisitos**: REQ-004
- **Entradas de diseño**: `PlanBDI`, biblioteca Π y requisito de cuota agotada.
- **Descripción**: registrar el runbook principal de autoescalado y el alternativo de degradación elegante para `ESTABILIZAR_RENDIMIENTO_SLA`. Seleccionar únicamente planes cuya precondición aplique y que no estén marcados como fallidos. Si se agota la cuota, marcar inviable el plan principal, conservar la intención actual y seleccionar automáticamente el Circuit Breaker, evitando reintentos repetidos del plan fallido.

### Fase 3: Q-Learning (Semana 04)

#### Paso 3.1: Completar el Gridworld estocástico y sus recompensas
- **Requisitos**: REQ-005
- **Entradas de diseño**: entorno 4×4 de la plantilla, mapa de hoyos/meta y dos modalidades de recompensa.
- **Descripción**: implementar movimientos acotados al tablero. En cada paso, ejecutar la acción elegida con probabilidad 1/3 y una de las dos desviaciones laterales con probabilidad 2/3. Terminar el episodio al llegar a un hoyo o a la meta. En modo estándar, entregar +1 en meta y 0 en las demás celdas terminales o normales; con shaping, usar −0.01 por paso, −1 en hoyo y +1 en meta.

#### Paso 3.2: Implementar aprendizaje TD y exploración ε-greedy
- **Requisitos**: REQ-006
- **Entradas de diseño**: ecuaciones explícitas de Q-Learning y parámetros de la plantilla.
- **Descripción**: crear la tabla Q de 16×4, seleccionar acciones con ε-greedy, aplicar `ε ← max(0.01, ε × 0.995)` por episodio y actualizar con TD-Error usando α=0.8 y γ=0.95 por defecto. No acumular valor futuro desde estados terminales.

#### Paso 3.3: Comparar los esquemas de recompensa por bloques
- **Requisitos**: REQ-007
- **Entradas de diseño**: 2000 episodios por defecto y comparación estándar/shaping.
- **Descripción**: entrenar ambos modos de forma independiente, registrar si cada episodio alcanza la meta y mostrar en consola la tasa media de éxito por bloque, además de las tablas Q del estado inicial. Usar una semilla configurable para hacer reproducible la comparación sin eliminar la estocasticidad.

### Fase 4: Validación y entrega

#### Paso 4.1: Verificar sintaxis, ejecución y criterios de aceptación
- **Requisitos**: REQ-001 a REQ-007
- **Entradas de diseño**: instrucciones generales y rúbrica de la práctica.
- **Descripción**: ejecutar por separado ambos scripts, comprobar sintaxis sin errores y revisar sus salidas. Confirmar inferencia antes del umbral del 80%, prioridades y fallback con intención preservada, actualización TD y decaimiento de ε, recompensas de ambos entornos y reporte de éxito por bloques.

## Estructura del proyecto

```text
.
├── README.md
├── practica4.md
├── practica_semana03_bdi.py
├── practica_semana04_rl.py
├── plan.md
├── research.md
└── checkpoints/
    ├── plan-to-tasks.yaml
    └── spec-to-plan.yaml
```

## Estrategia de validación

- **Tipo de aplicación**: scripts de consola independientes.
- **Recorridos críticos**:
  1. Ingresar tres lecturas CPU que cumplan la regla de crecimiento y activar la creencia antes del 80%.
  2. Confirmar el orden de prioridades y que la intención elegida es la de mayor prioridad disponible.
  3. Agotar la cuota durante el plan principal y comprobar el cambio al fallback conservando la intención.
  4. Ejecutar una transición del Gridworld que termine en hoyo o meta y verificar recompensa y estado terminal.
  5. Entrenar ambos entornos y confirmar que se imprime la tasa de éxito media por bloques.
- **Validación principal**: ejecución directa de ambos scripts y verificación de sus salidas; revisión sintáctica de cada archivo.
- **Datos reproducibles**: semilla configurable para `random` y NumPy, si se usa el generador aleatorio de NumPy.
- **Criterio de aceptación**: todos los criterios anteriores observables; no se exige un porcentaje de convergencia fijo porque la guía no define un umbral cuantitativo.
- **Brecha conocida**: la guía no indica umbrales para clasificar latencia como problema de caché o de SLA. Antes de codificar esas condiciones, acordar valores con el docente o mantenerlos como parámetros claramente identificados.

## Desglose de tareas

### Fase 1: Preparación

- [x] T001 [Plan:1.1] Crear `practica_semana03_bdi.py` y `practica_semana04_rl.py` con imports, clases/funciones de la plantilla y puntos de entrada independientes.

### Fase 2: Agente BDI

- [x] T002 [P] [Plan:2.1] Implementar en `practica_semana03_bdi.py` la ventana de tres valores y la inferencia de anomalía con CPU creciente y ambos incrementos consecutivos >15 puntos porcentuales.
- [x] T003 [Plan:2.2] Implementar `options()` y `filter()` en `practica_semana03_bdi.py` con los deseos, condiciones disponibles y prioridades 100, 80, 75 y 60.
- [x] T004 [Plan:2.3] Registrar los dos planes SLA e implementar selección de plan y conmutación por cuota en `practica_semana03_bdi.py`, preservando `intencion_actual` y excluyendo el plan fallido.

### Fase 3: Q-Learning

- [x] T005 [P] [Plan:3.1] Completar `EntornoGridworldEstocastico` en `practica_semana04_rl.py` con transiciones 1/3–2/3, límites del tablero, estados terminales y ambas funciones de recompensa.
- [x] T006 [Plan:3.2] Implementar en `practica_semana04_rl.py` la selección ε-greedy, el decaimiento de ε y la actualización Q mediante TD-Error.
- [x] T007 [Plan:3.3] Añadir a `practica_semana04_rl.py` la medición de éxitos por bloque y el reporte reproducible de ambos experimentos.

### Fase 4: Validación y entrega

- [x] T008 [Plan:4.1] Ejecutar los dos scripts por separado y verificar sintaxis, inferencia BDI, fallback, ecuación TD, recompensas y reporte de tasas de éxito.

## Mapeo de requisitos

| REQ ID | Descripción | Elementos del plan | Evidencia de implementación |
|--------|-------------|--------------------|-----------------------------|
| REQ-001 | Mantener dos ejercicios Python independientes y justificarlos con comentarios | 1.1, 4.1 | `practica_semana03_bdi.py`, `practica_semana04_rl.py` |
| REQ-002 | Mantener ventana CPU de tres lecturas e inferir anomalía bajo el 80% con la regla aclarada | 2.1, 4.1 | `AgenteBDI_Estudiante.brf()` en `practica_semana03_bdi.py` |
| REQ-003 | Activar deseos BDI y respetar las prioridades indicadas | 2.2, 4.1 | `AgenteBDI_Estudiante.options()` y `filter()` en `practica_semana03_bdi.py` |
| REQ-004 | Usar el plan alternativo al agotarse la cuota sin perder la intención | 2.3, 4.1 | `seleccionar_plan_fallback()` y biblioteca de planes en `practica_semana03_bdi.py` |
| REQ-005 | Simular Gridworld estocástico y recompensas estándar y con shaping | 3.1, 4.1 | `EntornoGridworldEstocastico.step()` en `practica_semana04_rl.py` |
| REQ-006 | Aplicar Q-Learning TD y exploración ε-greedy con decaimiento especificado | 3.2, 4.1 | `entrenar_q_learning()` en `practica_semana04_rl.py` |
| REQ-007 | Comparar tasas de éxito medias por bloques y presentar el reporte de consola | 3.3, 4.1 | rutina de evaluación y salida de `practica_semana04_rl.py` |
