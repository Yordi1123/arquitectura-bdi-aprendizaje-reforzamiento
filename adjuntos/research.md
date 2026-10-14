# Decisiones y aclaraciones de la práctica

## Regla de inferencia de CPU

- **Decisión**: usar tres lecturas estrictamente crecientes y exigir que cada diferencia consecutiva sea mayor que 15 puntos porcentuales.
- **Fundamento**: el enunciado dice “por ciclo”; el comentario de la plantilla sugiere una diferencia acumulada distinta. El usuario aclaró que debe exigirse el incremento en cada ciclo.
- **Alternativa descartada**: diferencia acumulada `p3 - p1 >= 15`, porque permitiría incrementos individuales menores o iguales a 15.

## Deseos asociados a latencia

- **Decisión de planificación**: parametrizar los umbrales para las condiciones de caché/SLA y no fijar un número.
- **Fundamento**: la práctica contiene `latencia_ms`, pero no define límites ni una creencia explícita de estado de caché.
- **Alternativa descartada**: introducir un umbral numérico arbitrario como si fuera requisito.
- **Pendiente para implementación**: confirmar con el docente los límites de latencia; si no hay valor disponible, mantener los parámetros identificados como provisionales.

## Creencia derivada de la ventana

- **Decisión**: reevaluar `anomalia_fuga_memoria` a partir de la ventana vigente; si la ventana no cumple la regla, la creencia deja de estar derivada.
- **Fundamento**: la regla depende de las últimas tres lecturas, no de que el agente haya detectado alguna vez un patrón.
- **Alternativa**: conservar la creencia latched hasta una acción de recuperación; esa política no está indicada en la práctica.

## Transiciones y actualización terminal

- **Decisión**: modelar probabilidad 1/3 para la acción deseada y 2/3 para las desviaciones laterales; omitir el valor futuro en el TD-target cuando el siguiente estado sea terminal.
- **Fundamento**: coincide con la tasa solicitada y evita bootstrap desde estados terminales. La plantilla aproxima el 33.3% con umbrales decimales y usa la misma fórmula incluso en terminales.
