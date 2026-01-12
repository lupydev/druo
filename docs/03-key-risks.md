# Key Risks: Automatic Payment Retry Logic

## Resumen Ejecutivo de Riesgos

| Categoría   | Riesgo Alto | Riesgo Medio | Riesgo Bajo |
| ----------- | ----------- | ------------ | ----------- |
| Técnico     | 2           | 2            | 1           |
| Negocio     | 1           | 2            | 1           |
| Regulatorio | 1           | 1            | 0           |

---

## Riesgos Técnicos

### 🔴 ALTO: Rate Limit Violations con Procesadores

| Aspecto          | Detalle                                                                             |
| ---------------- | ----------------------------------------------------------------------------------- |
| **Descripción**  | Exceder límites de retry puede resultar en bloqueo de cuenta o penalizaciones       |
| **Probabilidad** | Media                                                                               |
| **Impacto**      | Alto - Podría afectar todos los pagos, no solo retries                              |
| **Trigger**      | Stripe: >5 retries por tarjeta en 24h, otros procesadores tienen límites diferentes |

**Mitigación:**

1. Implementar contador de retries por tarjeta con TTL de 24h en Redis
2. Rate limiter por procesador configurable
3. Circuit breaker que detenga retries si detectamos errores de rate limit
4. Alertas cuando alcancemos 80% del límite

**Plan de Contingencia:**

- Kill switch para desactivar retries globalmente en < 5 minutos
- Comunicación pre-establecida con account managers de procesadores

---

### 🔴 ALTO: Retry de Pagos que NO deberían reintentarse

| Aspecto          | Detalle                                                          |
| ---------------- | ---------------------------------------------------------------- |
| **Descripción**  | Reintentar pagos marcados como fraude o tarjeta robada           |
| **Probabilidad** | Media                                                            |
| **Impacto**      | Alto - Riesgo de fraude, problemas legales, pérdida de confianza |
| **Trigger**      | Clasificación incorrecta del tipo de fallo                       |

**Mitigación:**

1. Whitelist explícita de códigos de error retriable (no blacklist)
2. Mapeo exhaustivo de códigos de error por procesador
3. Review manual de cualquier código de error nuevo/desconocido
4. Flag automático para review si código no está en mapeo

**Plan de Contingencia:**

- Los códigos desconocidos NO se reintentan por defecto
- Alertas inmediatas para códigos no mapeados
- Proceso de escalación a Risk team

---

### 🟡 MEDIO: Fallo en Job Scheduler

| Aspecto          | Detalle                                                           |
| ---------------- | ----------------------------------------------------------------- |
| **Descripción**  | El scheduler de retries falla y no ejecuta reintentos programados |
| **Probabilidad** | Baja                                                              |
| **Impacto**      | Alto - Retries no se ejecutan, GMV perdido                        |
| **Trigger**      | Fallo de infraestructura, bug en scheduler                        |

**Mitigación:**

1. Health checks cada 1 minuto en scheduler
2. Heartbeat logging para detectar scheduler muerto
3. Redundancia: scheduler secundario en standby
4. Retries almacenados en PostgreSQL (persistentes) no solo en memoria

**Plan de Contingencia:**

- Script manual para procesar retries pendientes
- Runbook de recovery documentado
- Alerta PagerDuty para scheduler down

---

### 🟡 MEDIO: Inconsistencia de Estado de Pago

| Aspecto          | Detalle                                                           |
| ---------------- | ----------------------------------------------------------------- |
| **Descripción**  | Estado de pago en nuestra DB no coincide con estado en procesador |
| **Probabilidad** | Media                                                             |
| **Impacto**      | Medio - Podría causar doble cobro o retry innecesario             |
| **Trigger**      | Webhook perdido, timeout durante actualización, race condition    |

**Mitigación:**

1. Idempotency keys obligatorias en todos los retries
2. Reconciliación periódica con procesadores (cada 1h para pagos recientes)
3. Estado "pending_verification" antes de confirmar éxito/fallo
4. Retry con verificación previa del estado actual

**Plan de Contingencia:**

- Job de reconciliación manual disponible
- Logs detallados para debugging
- Proceso de refund automatizado si detectamos doble cobro

---

### 🟢 BAJO: Performance Degradation

| Aspecto          | Detalle                                                     |
| ---------------- | ----------------------------------------------------------- |
| **Descripción**  | Alto volumen de retries impacta performance general         |
| **Probabilidad** | Baja                                                        |
| **Impacto**      | Medio                                                       |
| **Trigger**      | Spike inusual de fallos, procesador con downtime prolongado |

**Mitigación:**

1. Cola separada para retries (no compite con pagos nuevos)
2. Rate limiting configurable en retries
3. Backpressure automático basado en queue depth
4. Auto-scaling para workers de retry

---

## Riesgos de Negocio

### 🔴 ALTO: ROI Negativo por Costos de Retry

| Aspecto          | Detalle                                                        |
| ---------------- | -------------------------------------------------------------- |
| **Descripción**  | Costos de intentos fallidos superan valor de pagos recuperados |
| **Probabilidad** | Baja                                                           |
| **Impacto**      | Alto - Pérdida financiera directa                              |
| **Trigger**      | Tasas de recuperación menores a las proyectadas, fees altos    |

**Mitigación:**

1. Análisis de costo por retry antes de lanzamiento
2. Límite máximo de retries configurable (default: 3)
3. Dashboard de ROI en tiempo real: costo de retries vs valor recuperado
4. Threshold automático para pausar retries si ROI < 0

**Plan de Contingencia:**

- Reducir número máximo de retries
- Ser más selectivo en qué fallos reintentar
- Negociar mejores tarifas con procesadores

---

### 🟡 MEDIO: Adopción Baja de Comerciantes

| Aspecto          | Detalle                                                   |
| ---------------- | --------------------------------------------------------- |
| **Descripción**  | Comerciantes no activan retry o lo desactivan rápidamente |
| **Probabilidad** | Media                                                     |
| **Impacto**      | Medio - No se captura el valor esperado                   |
| **Trigger**      | UX confusa, falta de confianza, falta de visibilidad      |

**Mitigación:**

1. Retry activado por defecto con opt-out (en lugar de opt-in)
2. Comunicación clara del valor y cómo funciona
3. Dashboard con métricas de recuperación visibles
4. Onboarding personalizado para comerciantes top

**Plan de Contingencia:**

- Sesiones de feedback con comerciantes que desactiven
- Iteración rápida en UX basada en feedback
- Incentivos para early adopters

---

### 🟡 MEDIO: Quejas de Clientes Finales

| Aspecto          | Detalle                                                   |
| ---------------- | --------------------------------------------------------- |
| **Descripción**  | Clientes finales se quejan de múltiples intentos de cobro |
| **Probabilidad** | Media                                                     |
| **Impacto**      | Medio - Afecta reputación de comerciante y Novo           |
| **Trigger**      | Notificaciones bancarias de intentos, confusión           |

**Mitigación:**

1. Delays apropiados entre intentos (no inmediatos para fondos insuficientes)
2. Documentación clara para comerciantes sobre cómo comunicar a clientes
3. Límite máximo de intentos visible
4. Templates de comunicación para comerciantes

---

### 🟢 BAJO: Competencia lanza feature similar

| Aspecto          | Detalle                                              |
| ---------------- | ---------------------------------------------------- |
| **Descripción**  | Competidor lanza retry automático antes que nosotros |
| **Probabilidad** | Baja                                                 |
| **Impacto**      | Bajo - Ya es feature estándar en industria           |

**Mitigación:**

- Mantener timeline agresivo de 6 semanas
- Diferenciarse en configurabilidad y transparencia

---

## Riesgos Regulatorios

### 🔴 ALTO: Incumplimiento PCI-DSS

| Aspecto          | Detalle                                           |
| ---------------- | ------------------------------------------------- |
| **Descripción**  | Logging o manejo de retry viola estándares PCI    |
| **Probabilidad** | Baja                                              |
| **Impacto**      | Muy Alto - Pérdida de certificación, multas       |
| **Trigger**      | Loguear datos de tarjeta, almacenamiento inseguro |

**Mitigación:**

1. NO loguear PAN, CVV, ni datos sensibles de tarjeta
2. Solo almacenar tokens y últimos 4 dígitos
3. Review de compliance antes de lanzamiento
4. Audit trail con datos no-sensibles únicamente

**Plan de Contingencia:**

- Pause de feature hasta remediación
- Consultoría externa de PCI si hay dudas

---

### 🟡 MEDIO: Regulaciones Locales LATAM

| Aspecto          | Detalle                                                  |
| ---------------- | -------------------------------------------------------- |
| **Descripción**  | Cada país puede tener reglas diferentes sobre reintentos |
| **Probabilidad** | Media                                                    |
| **Impacto**      | Medio - Podría requerir desactivar en ciertos países     |
| **Trigger**      | Regulación de protección al consumidor, leyes bancarias  |

**Mitigación:**

1. Review legal por país antes de rollout en ese país
2. Configuración de retry por país
3. Empezar con países de menor riesgo regulatorio
4. Kill switch por país

---

## Matriz de Riesgos Consolidada

```
              IMPACTO
           Bajo   Medio   Alto
        ┌───────┬───────┬───────┐
   Alta │       │       │       │
        ├───────┼───────┼───────┤
PROB.   │       │ R5,R6 │ R1,R2 │
  Media ├───────┼───────┼───────┤
        │       │ R4,R7 │ R3    │
   Baja ├───────┼───────┼───────┤
        │ R8    │       │ R9    │
        └───────┴───────┴───────┘

R1: Rate Limit Violations
R2: Retry de pagos no-retriable
R3: ROI Negativo
R4: Inconsistencia de estado
R5: Adopción baja
R6: Quejas de clientes
R7: Regulaciones LATAM
R8: Competencia
R9: PCI-DSS
```

---

## Plan de Monitoreo de Riesgos

| Riesgo      | Indicador de Alerta         | Threshold | Acción                          |
| ----------- | --------------------------- | --------- | ------------------------------- |
| Rate Limits | Retries/tarjeta/24h         | > 4       | Pausar retries para esa tarjeta |
| Wrong Retry | Códigos no mapeados         | > 0       | Review manual inmediato         |
| ROI         | Costo/Valor recuperado      | > 0.8     | Revisar estrategia              |
| Scheduler   | Heartbeat                   | Miss > 2  | Alerta PagerDuty                |
| Adopción    | % comerciantes con retry ON | < 50%     | Investigar causas               |
