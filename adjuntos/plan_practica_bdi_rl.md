# 🤖 Plan de Desarrollo — Práctica BDI + Aprendizaje por Reforzamiento
**Curso:** Agentes Inteligentes — 8vo Ciclo | Universidad Nacional del Santa  
**Semanas:** 03 – 04 | **Tema:** Arquitectura BDI integrada con Q-Learning

---

## 📋 Análisis de Rúbricas y Ponderación

| # | Criterio | Descripción | Peso |
|---|----------|-------------|------|
| 1 | **Modelado BDI Formal** | Correcta definición de Creencias, Deseos e Intenciones + ciclo deliberativo | **25%** |
| 2 | **Implementación de RL** | MDP bien formulado, función de recompensa y actualización correcta de Q(s,a) | **30%** |
| 3 | **Integración BDI + RL** | Sinergia entre deliberación BDI y política ε-greedy del RL | **25%** |
| 4 | **Experimentación y Reporte** | Pruebas, hiperparámetros α/γ/ε, gráficas de convergencia y análisis crítico | **20%** |

> [!IMPORTANT]
> El criterio de mayor peso (30%) es la **Implementación de RL**. Asegúrate de que la ecuación de Bellman esté correctamente implementada.

---

## 🏗️ Arquitectura del Proyecto

```
arquitectura-bdi-aprendizaje-reforzamiento/
│
├── environment.py        # Entorno GridWorld (estados, transiciones, recompensas)
├── agent_bdi.py          # Clases BDI: BeliefBase, DesireSet, IntentionStack + ciclo
├── q_learning.py         # Algoritmo Q-Learning + política ε-greedy
├── main.py               # Orquestador: bucle de entrenamiento + visualización
├── utils.py              # Gráficas matplotlib, métricas
└── README.md             # Documentación del proyecto
```

---

## 🔵 FASE 1 — Modelado BDI Formal (Rúbrica 1: 25%)

### Objetivo
Definir estructuras de datos que representen los tres componentes mentales del agente.

### Entregables clave en `agent_bdi.py`

```python
# ============================================================
# 1. BASE DE CREENCIAS (Beliefs) — B
# ============================================================
class BeliefBase:
    """Representa el conocimiento actual del agente sobre el mundo."""
    def __init__(self):
        self.beliefs = {}          # dict: {variable: valor}
    
    def update(self, perception: dict):
        """Revisión de creencias basada en nueva percepción."""
        self.beliefs.update(perception)
    
    def get(self, key, default=None):
        return self.beliefs.get(key, default)

# ============================================================
# 2. CONJUNTO DE DESEOS (Desires) — D
# ============================================================
class DesireSet:
    """Conjunto de metas que el agente querría alcanzar."""
    def __init__(self, goals: list):
        self.goals = goals         # lista de estados-meta
    
    def generate(self, beliefs: BeliefBase) -> list:
        """Filtra metas alcanzables dado el estado de creencias."""
        return [g for g in self.goals if self._is_achievable(g, beliefs)]
    
    def _is_achievable(self, goal, beliefs):
        # Criterio: meta no alcanzada aún + posición actual no bloqueada
        current_pos = beliefs.get('position')
        return current_pos != goal

# ============================================================
# 3. PILA DE INTENCIONES (Intentions) — I
# ============================================================
class IntentionStack:
    """Intenciones actuales del agente (compromisos de acción)."""
    def __init__(self):
        self.stack = []
    
    def select(self, desires: list, q_table: dict, state):
        """Selecciona la intención más prometedora guiada por Q-values."""
        # Ordenar deseos por Q-value estimado hacia ese goal
        self.stack = sorted(desires, key=lambda g: q_table.get((state, g), 0.0), reverse=True)
    
    def current(self):
        return self.stack[0] if self.stack else None
```

### Ciclo Deliberativo BDI Completo

```python
class BDIAgent:
    def bdi_cycle(self, perception):
        # 1. SENSE  → Actualizar creencias
        self.beliefs.update(perception)
        
        # 2. OPTIONS → Generar deseos viables
        active_desires = self.desires.generate(self.beliefs)
        
        # 3. FILTER → Adoptar intenciones (guiado por Q-table)
        state = self.beliefs.get('position')
        self.intentions.select(active_desires, self.q_table, state)
        
        # 4. EXECUTE → Seleccionar acción con ε-greedy
        action = self.choose_action(state)
        return action
```

> [!TIP]
> Para la rúbrica 1, el evaluador verificará que las **tres clases** (BeliefBase, DesireSet, IntentionStack) estén diferenciadas y cumplan su rol específico.

---

## 🟠 FASE 2 — Implementación Q-Learning / RL (Rúbrica 2: 30%)

### Entorno GridWorld en `environment.py`

```python
import numpy as np

class GridWorld:
    """Entorno de cuadrícula NxN con obstáculos y meta."""
    
    def __init__(self, size=5, start=(0,0), goal=(4,4), obstacles=None):
        self.size = size
        self.start = start
        self.goal = goal
        self.obstacles = obstacles or [(1,1),(2,2),(3,1)]
        self.state = start
        
        # Acciones: 0=arriba, 1=abajo, 2=izquierda, 3=derecha
        self.actions = [0, 1, 2, 3]
        self.action_map = {
            0: (-1, 0),  # arriba
            1: ( 1, 0),  # abajo
            2: ( 0,-1),  # izquierda
            3: ( 0, 1),  # derecha
        }
    
    def reset(self):
        self.state = self.start
        return self.state
    
    def step(self, action):
        dr, dc = self.action_map[action]
        r, c = self.state
        new_r = max(0, min(self.size-1, r + dr))
        new_c = max(0, min(self.size-1, c + dc))
        new_state = (new_r, new_c)
        
        # Función de Recompensa R(s, a, s')
        if new_state in self.obstacles:
            reward = -10     # Penalización por obstáculo
            new_state = self.state  # Rebote (no avanza)
        elif new_state == self.goal:
            reward = +100    # Recompensa por alcanzar meta
        else:
            reward = -1      # Penalización por tiempo (incentiva eficiencia)
        
        self.state = new_state
        done = (new_state == self.goal)
        return new_state, reward, done
```

### Algoritmo Q-Learning en `q_learning.py`

```python
import random

class QLearningAgent:
    """Implementación del algoritmo Q-Learning tabular."""
    
    def __init__(self, actions, alpha=0.1, gamma=0.99, epsilon=1.0, epsilon_decay=0.995, epsilon_min=0.01):
        self.actions     = actions
        self.alpha       = alpha        # Tasa de aprendizaje
        self.gamma       = gamma        # Factor de descuento
        self.epsilon     = epsilon      # Tasa de exploración
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
        self.q_table     = {}           # Q(s, a)
    
    def get_q(self, state, action):
        return self.q_table.get((state, action), 0.0)
    
    def choose_action(self, state):
        """Política ε-greedy: exploración vs. explotación."""
        if random.random() < self.epsilon:
            return random.choice(self.actions)   # Explorar
        return self._best_action(state)           # Explotar
    
    def _best_action(self, state):
        q_values = [self.get_q(state, a) for a in self.actions]
        return self.actions[q_values.index(max(q_values))]
    
    def update(self, state, action, reward, next_state):
        """Ecuación de Bellman — Actualización de Q-table."""
        best_next_q = max([self.get_q(next_state, a) for a in self.actions])
        current_q   = self.get_q(state, action)
        
        # Q(s,a) ← Q(s,a) + α[R + γ·max Q(s',a') - Q(s,a)]
        new_q = current_q + self.alpha * (reward + self.gamma * best_next_q - current_q)
        self.q_table[(state, action)] = new_q
    
    def decay_epsilon(self):
        """Reduce ε gradualmente → más explotación conforme aprende."""
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
```

> [!IMPORTANT]
> La **ecuación de Bellman** debe estar explícitamente comentada en el código. El evaluador verifica que `α`, `γ` y `ε` sean parámetros configurables.

---

## 🟢 FASE 3 — Integración BDI + RL (Rúbrica 3: 25%)

### El punto de integración: `agent_bdi.py` completo

La clave es que las **Intenciones** del BDI son **guiadas por los Q-values** aprendidos:

```python
class BDIAgent:
    """
    Agente BDI híbrido que integra razonamiento deliberativo
    con aprendizaje por reforzamiento (Q-Learning).
    """
    
    def __init__(self, env, goals):
        self.beliefs    = BeliefBase()
        self.desires    = DesireSet(goals)
        self.intentions = IntentionStack()
        self.rl_agent   = QLearningAgent(actions=env.actions)
        self.env        = env
    
    def run_episode(self):
        """Ejecuta un episodio completo del ciclo BDI+RL."""
        state = self.env.reset()
        total_reward = 0
        done = False
        steps = 0
        
        while not done and steps < 200:
            # --- CICLO BDI ---
            perception = {'position': state}
            
            # 1. SENSE: Actualizar creencias
            self.beliefs.update(perception)
            
            # 2. OPTIONS: Generar deseos viables
            active_desires = self.desires.generate(self.beliefs)
            
            # 3. FILTER: Seleccionar intención guiada por Q-values
            self.intentions.select(active_desires, self.rl_agent.q_table, state)
            
            # 4. EXECUTE: Elegir acción con política ε-greedy
            action = self.rl_agent.choose_action(state)
            
            # --- INTERACCIÓN CON ENTORNO ---
            next_state, reward, done = self.env.step(action)
            
            # --- APRENDIZAJE RL ---
            self.rl_agent.update(state, action, reward, next_state)
            
            state = next_state
            total_reward += reward
            steps += 1
        
        # Reducir exploración al final del episodio
        self.rl_agent.decay_epsilon()
        return total_reward, steps
```

---

## 🟣 FASE 4 — Experimentación y Reporte (Rúbrica 4: 20%)

### Orquestador `main.py`

```python
import matplotlib.pyplot as plt
from environment import GridWorld
from agent_bdi import BDIAgent

def train(n_episodes=500):
    env    = GridWorld(size=5, start=(0,0), goal=(4,4))
    goals  = [(4,4)]
    agent  = BDIAgent(env, goals)
    
    rewards_per_episode = []
    steps_per_episode   = []
    
    for ep in range(n_episodes):
        reward, steps = agent.run_episode()
        rewards_per_episode.append(reward)
        steps_per_episode.append(steps)
        
        if (ep+1) % 50 == 0:
            avg = sum(rewards_per_episode[-50:]) / 50
            print(f"Episodio {ep+1:4d} | Recompensa promedio: {avg:7.2f} | ε={agent.rl_agent.epsilon:.3f}")
    
    return rewards_per_episode, steps_per_episode

def plot_results(rewards, steps):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
    
    # Curva de convergencia de recompensa
    ax1.plot(rewards, alpha=0.4, color='steelblue', label='Por episodio')
    # Media móvil
    window = 20
    moving_avg = [sum(rewards[max(0,i-window):i+1])/min(i+1,window) for i in range(len(rewards))]
    ax1.plot(moving_avg, color='red', linewidth=2, label=f'Media móvil ({window} ep)')
    ax1.set_xlabel('Episodio')
    ax1.set_ylabel('Recompensa total')
    ax1.set_title('Convergencia del Aprendizaje (BDI + Q-Learning)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Pasos por episodio (eficiencia)
    ax2.plot(steps, alpha=0.5, color='orange')
    ax2.set_xlabel('Episodio')
    ax2.set_ylabel('Pasos hasta terminar')
    ax2.set_title('Eficiencia del Agente por Episodio')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('resultados_entrenamiento.png', dpi=150)
    plt.show()

if __name__ == '__main__':
    rewards, steps = train(n_episodes=500)
    plot_results(rewards, steps)
```

### Experimentos a documentar

| Experimento | α (learning rate) | γ (descuento) | ε inicial | Episodios | Observación esperada |
|-------------|-------------------|---------------|-----------|-----------|----------------------|
| **Base** | 0.1 | 0.99 | 1.0 → 0.01 | 500 | Convergencia estándar |
| **Alta exploración** | 0.1 | 0.99 | 1.0 → 0.05 | 500 | Más lento pero robusto |
| **Descuento bajo** | 0.1 | 0.5  | 1.0 → 0.01 | 500 | Miope, peores soluciones |
| **LR alto** | 0.9 | 0.99 | 1.0 → 0.01 | 500 | Inestabilidad vs. rapidez |

---

## 📅 Cronograma Sugerido

```
SEMANA 03
├── Día 1-2: Diseño del entorno GridWorld (environment.py)
├── Día 3-4: Implementación Q-Learning (q_learning.py)
└── Día 5  : Pruebas unitarias del RL (verificar que aprende)

SEMANA 04
├── Día 1-2: Implementación ciclo BDI (agent_bdi.py)
├── Día 3  : Integración BDI + RL (main.py)
├── Día 4  : Ejecución de experimentos + gráficas
└── Día 5  : Redacción del reporte final
```

---

## ✅ Checklist Final — Verificación por Rúbrica

### Rúbrica 1 — Modelado BDI (25%)
- [ ] Clase `BeliefBase` con método `update()` implementado
- [ ] Clase `DesireSet` con lógica de filtrado de metas alcanzables
- [ ] Clase `IntentionStack` con selección de intención basada en Q-values
- [ ] Ciclo deliberativo completo: Sense → Options → Filter → Execute

### Rúbrica 2 — Implementación RL (30%)
- [ ] Entorno con espacio de estados y acciones bien definido
- [ ] Función de recompensa diferenciada (obstáculo, meta, paso)
- [ ] Ecuación de Bellman implementada correctamente
- [ ] Parámetros α, γ, ε configurables y documentados
- [ ] Política ε-greedy con decaimiento

### Rúbrica 3 — Integración BDI + RL (25%)
- [ ] Las intenciones BDI son guiadas por Q-values (conexión explícita)
- [ ] El ciclo BDI usa la política RL para ejecutar acciones
- [ ] El aprendizaje RL actualiza el comportamiento del agente en tiempo real

### Rúbrica 4 — Experimentación y Reporte (20%)
- [ ] Mínimo 3 configuraciones de hiperparámetros probadas
- [ ] Gráfica de convergencia de recompensa por episodio
- [ ] Gráfica de pasos/eficiencia por episodio
- [ ] Análisis crítico de resultados en el reporte
- [ ] Conclusiones sobre ventajas de BDI + RL vs. solo RL

---

## 📚 Conceptos Teóricos Clave a Mencionar en el Reporte

1. **Arquitectura BDI** (Bratman, Rao & Georgeff): El modelo mental del agente surge de la interacción entre $B$, $D$ e $I$.
2. **MDP** $(S, A, P, R, \gamma)$: Formalización matemática para toma de decisiones bajo incertidumbre.
3. **Ecuación de Bellman**:
   $$Q(s,a) \leftarrow Q(s,a) + \alpha \left[ R(s,a,s') + \gamma \max_{a'} Q(s',a') - Q(s,a) \right]$$
4. **Dilema Exploración vs. Explotación**: El parámetro $\epsilon$ controla este balance.
5. **Ventaja del híbrido BDI + RL**: El BDI aporta razonamiento orientado a metas; el RL aporta adaptación automática al entorno.
