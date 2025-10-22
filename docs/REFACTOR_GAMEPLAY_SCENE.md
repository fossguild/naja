# Refatoração do GameplayScene

## Problema Atual

O arquivo `gameplay.py` (933 linhas) viola princípios da arquitetura ECS ao misturar:
- Coordenação de sistemas (correto)
- Lógica de jogo (deveria estar em sistemas)
- Manipulação direta de componentes (deveria estar em sistemas)
- Inicialização complexa de entidades (deveria estar em prefabs/sistemas)

## Arquitetura Ideal

### Responsabilidade da Scene
Segundo a arquitetura ECS, uma Scene deve APENAS:
1. Registrar sistemas na ordem correta
2. Chamar `system.update(world)` em cada sistema
3. Gerenciar transições entre cenas
4. Chamar hooks de ciclo de vida (`on_attach`, `on_detach`, `on_enter`, `on_exit`)

### O que NÃO deve estar na Scene
- ❌ Lógica de jogo
- ❌ Manipulação direta de componentes
- ❌ Criação manual de entidades
- ❌ Aplicação de configurações
- ❌ Callbacks que implementam comportamento de jogo

## Plano de Refatoração

### Fase 1: Extrair Inicialização para Serviço
**Criar:** `src/game/services/game_initializer.py`
```python
class GameInitializer:
    """Serviço responsável por inicializar o estado do jogo."""
    
    def reset_world(self, world: World, settings, config) -> None:
        """Reset completo do mundo para novo jogo."""
        pass
    
    def create_initial_entities(self, world: World, settings) -> None:
        """Cria entidades iniciais (cobra, maçãs, obstáculos)."""
        pass
```

**Responsabilidades:**
- Limpar registry
- Criar entidades iniciais usando prefabs
- Aplicar configurações iniciais
- Gerenciar estado de game over

**Linhas movidas:** 362-456 (`_reset_game_world`)

---

### Fase 2: Criar SettingsApplySystem
**Criar:** `src/ecs/systems/settings_apply.py`
```python
class SettingsApplySystem(BaseSystem):
    """Sistema que aplica mudanças de configuração ao jogo."""
    
    def update(self, world: World) -> None:
        """Aplica configurações pendentes."""
        # Detectar mudanças em settings
        # Aplicar grid size, palette, speeds, obstacle difficulty
        pass
```

**Responsabilidades:**
- Detectar mudanças em settings
- Aplicar mudanças de tamanho de grid
- Aplicar mudanças de paleta
- Aplicar mudanças de velocidade
- Aplicar mudanças de dificuldade de obstáculos

**Linhas movidas:**
- 332-360 (`_apply_settings_to_world`)
- 739-758 (`_apply_snake_palette`)
- 760-783 (`_apply_initial_speed`)
- 785-811 (`_apply_max_speed`)
- 813-843 (`_apply_obstacle_difficulty`)

---

### Fase 3: Remover Callbacks Redundantes
Os callbacks atuais estão duplicando lógica que já deveria estar nos sistemas:

#### Callbacks a Remover
1. **`_handle_direction_change`** (linhas 558-565)
   - Já gerenciado pelo `InputSystem`
   
2. **`_get_current_direction`** (linhas 567-577)
   - Deveria ser query simples, não callback
   
3. **`_get_snake_head_position`** (linhas 603-611)
   - Deveria ser query simples, não callback
   
4. **`_get_snake_tail_positions`** (linhas 613-621)
   - Deveria ser query simples, não callback

5. **`_get_snake_next_position`** (linhas 623-643)
   - Lógica deveria estar no `MovementSystem`

#### Callbacks a Mover para Sistemas
1. **`_handle_death`** → Mover para `CollisionSystem`
   - Incluir lógica de reproduzir sons
   - Incluir lógica de transição de cena

2. **`_handle_apple_eaten`** → Mover para `CollisionSystem`
   - Incluir lógica de crescer cobra
   - Incluir lógica de incrementar score
   - Incluir lógica de reproduzir sons

3. **`_handle_speed_increase`** → Mover para `ScoringSystem`
   - Aplicar aumento de velocidade quando maçã é comida

---

### Fase 4: Simplificar Estrutura da Scene

#### Antes (933 linhas)
```python
class GameplayScene(BaseScene):
    # 100+ linhas de __init__
    # 50+ linhas de on_attach
    # 200+ linhas de update
    # 300+ linhas de callbacks
    # 200+ linhas de aplicação de settings
    # etc.
```

#### Depois (estimado ~150 linhas)
```python
class GameplayScene(BaseScene):
    """Coordena sistemas ECS durante gameplay."""
    
    def __init__(self, ...):
        # apenas inicialização simples
        pass
    
    def on_attach(self) -> None:
        # registrar sistemas em ordem
        pass
    
    def on_detach(self) -> None:
        # cleanup simples
        pass
    
    def update(self, dt_ms: float) -> Optional[str]:
        # atualizar sistemas em ordem
        # gerenciar pause
        pass
    
    def on_enter(self) -> None:
        # delegar para GameInitializer
        pass
    
    def on_exit(self) -> None:
        # cleanup simples
        pass
```

---

## Benefícios da Refatoração

### 1. Separação de Responsabilidades
- **Scene**: Apenas coordenação
- **Sistemas**: Lógica de jogo
- **Serviços**: Inicialização e configuração
- **Prefabs**: Criação de entidades

### 2. Testabilidade
- Cada sistema pode ser testado isoladamente
- Serviços podem ser mockados
- Scene fica trivial de testar

### 3. Manutenibilidade
- Arquivos menores e mais focados
- Mais fácil encontrar código específico
- Menos acoplamento entre componentes

### 4. Conformidade com ECS
- Respeita princípios da arquitetura
- Facilita onboarding de novos desenvolvedores
- Código mais previsível e padronizado

---

## Ordem de Implementação

1. ✅ **Criar GameInitializer** (baixo risco)
   - Extrair `_reset_game_world` para serviço
   - Testar isoladamente

2. ✅ **Criar SettingsApplySystem** (médio risco)
   - Extrair lógica de aplicação de settings
   - Adicionar ao pipeline de sistemas
   - Testar mudanças de settings

3. ✅ **Refatorar Callbacks** (alto risco)
   - Mover lógica para sistemas apropriados
   - Remover callbacks redundantes
   - Testar comportamento de jogo

4. ✅ **Simplificar GameplayScene** (baixo risco)
   - Remover código movido
   - Limpar imports
   - Adicionar documentação

---

