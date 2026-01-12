# MVP Scope: Automatic Payment Retry Logic

## Resumen de Constraints

| Constraint   | Valor                                         |
| ------------ | --------------------------------------------- |
| Timeline     | 6 semanas para MVP                            |
| Recursos     | 2 backend engineers @ 50% = 1 FTE equivalente |
| Procesadores | Stripe, PSE, Nequi (diferentes políticas)     |
| Rate Limits  | Stripe: max 5 retries por tarjeta por 24h     |

---

## Scope Definition

### ✅ MUST-HAVE (P0) - Sin esto no hay MVP

| Feature                    | Descripción                                               | Justificación                                         |
| -------------------------- | --------------------------------------------------------- | ----------------------------------------------------- |
| **Retry Engine Core**      | Motor que ejecuta reintentos automáticos basado en reglas | Core del producto, sin esto no hay valor              |
| **Failure Classification** | Clasificar fallos en retriable vs non-retriable           | Evita reintentar "tarjeta robada" y similares         |
| **Retry Scheduling**       | Programar reintentos: inmediato, 1h, 24h                  | Diferentes tipos de fallo requieren diferentes delays |
| **Rate Limit Compliance**  | Respetar límites de cada procesador (ej: 5/24h Stripe)    | Obligatorio para no ser bloqueados                    |
| **Audit Trail/Logging**    | Log de cada intento con timestamp, resultado, razón       | Requerido por Compliance/PCI-DSS                      |
| **Merchant Toggle**        | ON/OFF de retry automático por comerciante                | Control básico para comerciantes                      |
| **Stripe Integration**     | Implementación completa para Stripe                       | Procesador principal, mayor volumen                   |
| **Notificación Final**     | Notificar al comerciante en éxito/fallo final             | Visibilidad mínima requerida                          |

### 🟡 NICE-TO-HAVE (P1) - Mejora significativa pero no bloqueante

| Feature                     | Descripción                                             | Justificación                                      |
| --------------------------- | ------------------------------------------------------- | -------------------------------------------------- |
| **PSE Integration**         | Soporte para procesador PSE                             | Segundo procesador en volumen                      |
| **Nequi Integration**       | Soporte para procesador Nequi                           | Tercer procesador en volumen                       |
| **Configuration Dashboard** | UI para que comerciantes configuren reglas              | Mejora UX pero puede ser manual inicialmente       |
| **Retry Analytics**         | Dashboard con métricas de retry success rate            | Valioso para optimización pero no crítico para MVP |
| **Custom Retry Intervals**  | Permitir comerciantes definir intervalos personalizados | Flexibilidad adicional                             |
| **Failure Type Toggle**     | ON/OFF de retry por tipo de fallo específico            | Control granular                                   |

### ❌ OUT OF SCOPE - No para MVP

| Feature                                        | Razón de Exclusión                                                |
| ---------------------------------------------- | ----------------------------------------------------------------- |
| **ML para predicción de retry success**        | Complejidad alta, requiere data histórica, no viable en 6 semanas |
| **Retry para métodos de pago no-tarjeta**      | Foco inicial en tarjetas que representan mayor volumen            |
| **Notificaciones al cliente final**            | Complejidad de UX, requiere diseño extenso                        |
| **Multi-currency retry optimization**          | Optimización prematura                                            |
| **A/B testing framework**                      | Puede hacerse manualmente en rollout gradual                      |
| **Self-service onboarding**                    | Onboarding manual es aceptable para MVP                           |
| **Webhook para eventos de retry**              | API interna es suficiente para MVP                                |
| **Retry para pagos recurrentes/subscriptions** | Caso de uso diferente, complejidad adicional                      |
| **Mobile SDK updates**                         | No afecta backend retry logic                                     |
| **White-label customization**                  | No prioritario para validar hipótesis                             |

---

## Decisiones de Scope Críticas

### 1. Solo Stripe en MVP, luego PSE y Nequi

**Justificación**:

- Stripe tiene la mejor documentación y API más predecible
- Permite validar el modelo antes de escalar a procesadores más complejos
- Un procesador bien implementado > tres implementaciones parciales

### 2. Dashboard básico vs Dashboard completo

**Decisión**: Dashboard básico con toggle ON/OFF únicamente
**Justificación**:

- Configuración avanzada puede hacerse via soporte/admin inicialmente
- Reduce scope de frontend significativamente
- Permite validar qué configuraciones realmente necesitan los comerciantes

### 3. Retry intervals fijos vs configurables

**Decisión**: Intervals fijos por tipo de fallo en MVP
**Justificación**:

- Basados en best practices de la industria
- Simplifica implementación
- Configuración personalizada es nice-to-have

### 4. Notificaciones

**Decisión**: Solo notificación final (éxito o fallo después de agotar intentos)
**Justificación**:

- Evita spam de notificaciones intermedias
- Comerciante solo necesita saber el resultado final
- Reduce complejidad de integración

---

## Matriz de Priorización

```
                    IMPACTO
                    Alto    Bajo
              ┌─────────┬─────────┐
        Alto  │   P0    │   P1    │
ESFUERZO      │ HACER   │ EVALUAR │
              ├─────────┼─────────┤
        Bajo  │   P0    │   P2    │
              │ HACER   │ DESPUÉS │
              └─────────┴─────────┘
```

| Feature                 | Impacto            | Esfuerzo | Prioridad    |
| ----------------------- | ------------------ | -------- | ------------ |
| Retry Engine Core       | Alto               | Alto     | P0           |
| Failure Classification  | Alto               | Medio    | P0           |
| Stripe Integration      | Alto               | Medio    | P0           |
| Audit Trail             | Alto (compliance)  | Bajo     | P0           |
| Rate Limit Compliance   | Alto (obligatorio) | Bajo     | P0           |
| PSE Integration         | Medio              | Medio    | P1           |
| Configuration Dashboard | Medio              | Alto     | P1           |
| ML Prediction           | Alto               | Muy Alto | Out of Scope |

---

## Definition of Done para MVP

### Funcional

- [ ] El sistema detecta pagos fallidos automáticamente
- [ ] Los pagos retriable se reintentan según schedule configurado
- [ ] Los pagos non-retriable NO se reintentan
- [ ] Se respetan los rate limits de Stripe
- [ ] Los comerciantes pueden activar/desactivar retry

### No Funcional

- [ ] Todos los intentos están logueados con audit trail completo
- [ ] El sistema maneja 1000 reintentos/minuto sin degradación
- [ ] Tiempo de respuesta < 500ms para scheduling
- [ ] 99.9% uptime del retry scheduler

### Documentación

- [ ] Runbook de operaciones
- [ ] Documentación de API interna
- [ ] Guía de troubleshooting
