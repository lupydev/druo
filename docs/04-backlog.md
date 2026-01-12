# Backlog: Automatic Payment Retry Logic MVP

## Contexto de Capacidad

| Recurso                    | Disponibilidad       | Total Semanas |
| -------------------------- | -------------------- | ------------- |
| 2 Backend Engineers        | 50% cada uno         | 6 semanas     |
| **Capacidad Total**        | 1 FTE equivalente    | 6 semanas     |
| **Story Points Estimados** | ~30 SP (5 SP/semana) | -             |

### Sizing Guide

| Tamaño | Story Points | Días Dev (1 FTE) | Descripción                             |
| ------ | ------------ | ---------------- | --------------------------------------- |
| **S**  | 1-2          | 0.5-1 día        | Tarea simple, bajo riesgo               |
| **M**  | 3-5          | 2-3 días         | Complejidad moderada                    |
| **L**  | 8+           | 4-5 días         | Alta complejidad, múltiples componentes |

---

## Epic 1: Core Retry Engine

**Objetivo**: Motor central que detecta, clasifica y ejecuta reintentos

### E1.1 - Failure Detection Service

| Atributo         | Valor                                                                  |
| ---------------- | ---------------------------------------------------------------------- |
| **Prioridad**    | P0                                                                     |
| **Estimación**   | M (3 SP)                                                               |
| **Dependencias** | Ninguna                                                                |
| **Descripción**  | Servicio que escucha webhooks de procesadores y detecta pagos fallidos |

**Criterios de Aceptación:**

- [ ] Webhook endpoint para recibir eventos de Stripe
- [ ] Parser de eventos para identificar pagos fallidos
- [ ] Evento interno emitido cuando se detecta un fallo
- [ ] Logging de cada evento recibido

**Tareas Técnicas:**

1. Crear endpoint `/webhooks/stripe`
2. Implementar signature verification de Stripe
3. Parser de evento `payment_intent.payment_failed`
4. Emitir evento a cola interna

---

### E1.2 - Failure Classification Engine

| Atributo         | Valor                                                      |
| ---------------- | ---------------------------------------------------------- |
| **Prioridad**    | P0                                                         |
| **Estimación**   | M (5 SP)                                                   |
| **Dependencias** | E1.1                                                       |
| **Descripción**  | Clasifica fallos en categorías y determina si es retriable |

**Criterios de Aceptación:**

- [ ] Mapeo completo de códigos de error Stripe → categoría
- [ ] Decisión binaria: retriable / non-retriable
- [ ] Delay recomendado por tipo de fallo
- [ ] Manejo de códigos desconocidos (default: non-retriable)

**Mapeo de Fallos:**

```
insufficient_funds → RETRIABLE, delay: 24h
card_declined → RETRIABLE, delay: 1h
processing_error → RETRIABLE, delay: immediate
card_velocity_exceeded → RETRIABLE, delay: 24h
lost_card → NON_RETRIABLE
stolen_card → NON_RETRIABLE
expired_card → NON_RETRIABLE
fraudulent → NON_RETRIABLE
```

**Tareas Técnicas:**

1. Crear tabla `failure_code_mapping` en PostgreSQL
2. Implementar `FailureClassifier` service
3. API para agregar/modificar mapeos (admin only)
4. Tests para cada categoría

---

### E1.3 - Retry Scheduler

| Atributo         | Valor                                                 |
| ---------------- | ----------------------------------------------------- |
| **Prioridad**    | P0                                                    |
| **Estimación**   | L (8 SP)                                              |
| **Dependencias** | E1.2                                                  |
| **Descripción**  | Programa y ejecuta reintentos según schedule definido |

**Criterios de Aceptación:**

- [ ] Almacena retry jobs en PostgreSQL (persistencia)
- [ ] Ejecuta jobs en el tiempo programado (±30 segundos)
- [ ] Respeta rate limits de procesador
- [ ] Maneja fallos del scheduler gracefully
- [ ] Heartbeat cada 1 minuto

**Schedule por Defecto:**

```
Intento 1: Inmediato (para timeouts) o según delay del tipo
Intento 2: +1 hora
Intento 3: +24 horas
```

**Tareas Técnicas:**

1. Crear tabla `retry_jobs` con índice en `scheduled_at`
2. Implementar worker que procesa jobs pendientes
3. Implementar rate limiter con Redis
4. Health check endpoint `/health/scheduler`
5. Métricas de jobs procesados, pendientes, fallidos

---

### E1.4 - Payment Retry Executor

| Atributo         | Valor                                          |
| ---------------- | ---------------------------------------------- |
| **Prioridad**    | P0                                             |
| **Estimación**   | M (5 SP)                                       |
| **Dependencias** | E1.3                                           |
| **Descripción**  | Ejecuta el reintento de pago con el procesador |

**Criterios de Aceptación:**

- [ ] Verifica estado actual antes de reintentar
- [ ] Usa idempotency key para evitar duplicados
- [ ] Actualiza estado del pago según resultado
- [ ] Emite eventos de éxito/fallo

**Tareas Técnicas:**

1. Integración con Stripe API para confirmar PaymentIntent
2. Implementar verificación pre-retry
3. Manejo de respuestas y actualización de estado
4. Retry con exponential backoff para errores transitorios

---

## Epic 2: Rate Limiting & Compliance

**Objetivo**: Asegurar cumplimiento de límites y regulaciones

### E2.1 - Rate Limiter por Tarjeta

| Atributo         | Valor                                                                 |
| ---------------- | --------------------------------------------------------------------- |
| **Prioridad**    | P0                                                                    |
| **Estimación**   | M (3 SP)                                                              |
| **Dependencias** | E1.3                                                                  |
| **Descripción**  | Límite de reintentos por tarjeta respetando políticas de procesadores |

**Criterios de Aceptación:**

- [ ] Máximo 5 retries por tarjeta en ventana de 24h (Stripe)
- [ ] Contador persistido en Redis con TTL de 24h
- [ ] Bloquea retry si límite alcanzado
- [ ] Configurable por procesador

**Tareas Técnicas:**

1. Redis key pattern: `retry_count:{card_fingerprint}:{processor}`
2. Incremento atómico con TTL
3. Check antes de scheduling
4. Métricas de rate limit hits

---

### E2.2 - Audit Trail System

| Atributo         | Valor                                                  |
| ---------------- | ------------------------------------------------------ |
| **Prioridad**    | P0                                                     |
| **Estimación**   | M (3 SP)                                               |
| **Dependencias** | E1.4                                                   |
| **Descripción**  | Logging completo de todos los intentos para compliance |

**Criterios de Aceptación:**

- [ ] Log de cada intento con: timestamp, payment_id, attempt_number, result, failure_code
- [ ] NO loguear datos sensibles (PAN, CVV)
- [ ] Logs queryables en BigQuery
- [ ] Retención de 7 años (compliance)

**Campos del Audit Log:**

```json
{
  "event_id": "uuid",
  "timestamp": "ISO8601",
  "payment_id": "pay_xxx",
  "merchant_id": "mer_xxx",
  "attempt_number": 2,
  "action": "RETRY_EXECUTED",
  "result": "SUCCESS|FAILURE",
  "failure_code": "insufficient_funds",
  "processor": "stripe",
  "card_last4": "4242"
}
```

**Tareas Técnicas:**

1. Crear tabla `retry_audit_log` en PostgreSQL
2. Sync a BigQuery para análisis
3. Filtrado de datos sensibles
4. Índices para queries comunes

---

## Epic 3: Merchant Configuration

**Objetivo**: Dar control a comerciantes sobre retry behavior

### E3.1 - Merchant Retry Settings

| Atributo         | Valor                                                    |
| ---------------- | -------------------------------------------------------- |
| **Prioridad**    | P0                                                       |
| **Estimación**   | S (2 SP)                                                 |
| **Dependencias** | Ninguna (puede paralelo a Epic 1)                        |
| **Descripción**  | Modelo de datos y API para configuración por comerciante |

**Criterios de Aceptación:**

- [ ] Toggle ON/OFF de retry automático
- [ ] Configuración persiste en PostgreSQL
- [ ] Default: retry enabled para nuevos comerciantes
- [ ] API REST para update

**Modelo de Datos:**

```sql
CREATE TABLE merchant_retry_config (
  merchant_id VARCHAR PRIMARY KEY,
  retry_enabled BOOLEAN DEFAULT true,
  max_attempts INT DEFAULT 3,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

**Tareas Técnicas:**

1. Crear tabla y migrations
2. API endpoints CRUD
3. Cache en Redis para performance
4. Seed defaults para merchants existentes

---

### E3.2 - Basic Dashboard UI

| Atributo         | Valor                                            |
| ---------------- | ------------------------------------------------ |
| **Prioridad**    | P1                                               |
| **Estimación**   | M (5 SP)                                         |
| **Dependencias** | E3.1                                             |
| **Descripción**  | UI simple para que comerciantes configuren retry |

**Criterios de Aceptación:**

- [ ] Vista de configuración actual
- [ ] Toggle para activar/desactivar
- [ ] Guardado con feedback visual
- [ ] Responsive (mobile friendly)

**Wireframe Básico:**

```
┌─────────────────────────────────────┐
│ Automatic Payment Retry Settings    │
├─────────────────────────────────────┤
│                                     │
│ Enable automatic retry  [  ON  ]    │
│                                     │
│ Maximum attempts: 3                 │
│                                     │
│ Retry schedule:                     │
│ • Attempt 1: Immediate              │
│ • Attempt 2: After 1 hour           │
│ • Attempt 3: After 24 hours         │
│                                     │
│ [  Save Settings  ]                 │
│                                     │
└─────────────────────────────────────┘
```

---

## Epic 4: Notifications

**Objetivo**: Mantener comerciantes informados de resultados

### E4.1 - Final Status Notification

| Atributo         | Valor                                                          |
| ---------------- | -------------------------------------------------------------- |
| **Prioridad**    | P0                                                             |
| **Estimación**   | S (2 SP)                                                       |
| **Dependencias** | E1.4                                                           |
| **Descripción**  | Notificación al comerciante cuando retry tiene resultado final |

**Criterios de Aceptación:**

- [ ] Webhook a merchant cuando pago se recupera exitosamente
- [ ] Webhook cuando se agotan todos los intentos
- [ ] Incluye detalles: payment_id, attempts, final_status
- [ ] Retry de webhook si falla entrega

**Payload de Notificación:**

```json
{
  "event": "payment.retry_completed",
  "payment_id": "pay_xxx",
  "final_status": "succeeded",
  "total_attempts": 2,
  "recovered_amount": 15000,
  "currency": "usd"
}
```

---

## Vista de Dependencias

```
                    ┌──────────────────┐
                    │ E1.1 Failure     │
                    │ Detection        │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ E1.2 Failure     │
                    │ Classification   │
                    └────────┬─────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
              ▼                             ▼
     ┌──────────────────┐         ┌──────────────────┐
     │ E1.3 Retry       │         │ E2.1 Rate        │
     │ Scheduler        │◄────────│ Limiter          │
     └────────┬─────────┘         └──────────────────┘
              │
              ▼
     ┌──────────────────┐         ┌──────────────────┐
     │ E1.4 Retry       │────────►│ E2.2 Audit       │
     │ Executor         │         │ Trail            │
     └────────┬─────────┘         └──────────────────┘
              │
              ▼
     ┌──────────────────┐
     │ E4.1 Final       │
     │ Notification     │
     └──────────────────┘

     ┌──────────────────┐         ┌──────────────────┐
     │ E3.1 Merchant    │────────►│ E3.2 Dashboard   │
     │ Settings (API)   │         │ UI               │
     └──────────────────┘         └──────────────────┘
```

---

## Sprint Planning (6 Semanas)

### Week 1-2: Foundation

| Item                        | SP     | Owner |
| --------------------------- | ------ | ----- |
| E1.1 Failure Detection      | 3      | Dev 1 |
| E1.2 Failure Classification | 5      | Dev 1 |
| E3.1 Merchant Settings      | 2      | Dev 2 |
| **Total**                   | **10** |       |

### Week 3-4: Core Engine

| Item                 | SP     | Owner         |
| -------------------- | ------ | ------------- |
| E1.3 Retry Scheduler | 8      | Dev 1 + Dev 2 |
| E2.1 Rate Limiter    | 3      | Dev 2         |
| **Total**            | **11** |               |

### Week 5: Execution & Compliance

| Item                | SP    | Owner |
| ------------------- | ----- | ----- |
| E1.4 Retry Executor | 5     | Dev 1 |
| E2.2 Audit Trail    | 3     | Dev 2 |
| **Total**           | **8** |       |

### Week 6: Polish & Beta

| Item                       | SP    | Owner |
| -------------------------- | ----- | ----- |
| E4.1 Notifications         | 2     | Dev 1 |
| E3.2 Dashboard UI (básico) | 5     | Dev 2 |
| Testing & Bug fixes        | -     | Ambos |
| **Total**                  | **7** |       |

---

## Definition of Ready (DoR)

Antes de que un item entre a sprint:

- [ ] Criterios de aceptación claros
- [ ] Dependencias identificadas y resueltas (o en progreso)
- [ ] Estimación acordada por el equipo
- [ ] Sin blockers conocidos
- [ ] Diseño técnico documentado (para items L)

## Definition of Done (DoD)

Para considerar un item completado:

- [ ] Código implementado y funcionando
- [ ] Tests unitarios con >80% coverage
- [ ] Code review aprobado
- [ ] Documentación actualizada
- [ ] Deployed en staging
- [ ] QA básico pasado
