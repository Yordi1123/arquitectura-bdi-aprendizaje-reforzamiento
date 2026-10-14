# arquitectura-bdi-aprendizaje-reforzamiento
Práctica de laboratorio del curso 'Agentes Inteligentes': implementación de una arquitectura BDI integrada con aprendizaje por refuerzo.

## Ejecución

Los ejercicios se implementan en programas independientes:

```powershell
python practica_semana03_bdi.py
python practica_semana04_rl.py
```

El ejercicio de Q-Learning requiere NumPy. Instálalo en el entorno de Python usado
para ejecutar la práctica si aún no está disponible:

```powershell
python -m pip install numpy
```

La simulación de Q-Learning usa una semilla fija (`42`) para reproducir la
comparación; puedes pasar otra semilla a `ejecutar_experimento` o
`entrenar_q_learning`. Los límites de latencia del agente BDI son opcionales
porque la especificación no proporciona valores.
