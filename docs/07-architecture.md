# Arquitectura de la Solución: Automatic Payment Retry Logic

## Diagrama de Arquitectura General

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              EXTERNAL SERVICES                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                  │
│   │   STRIPE    │     │     PSE     │     │    NEQUI   │                  │
│   │  (Primary)  │     │   (P1)      │     │    (P1)    │                  │
│   └──────┬──────┘     └─────────────┘     └─────────────┘                  │
│          │                                                                  │
│          │ Webhooks (payment_failed)                                        │
└──────────┼──────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             NOVO INFRASTRUCTURE                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        API GATEWAY (Kong/AWS ALB)                     │  │
│  └──────────────────────────────────────┬───────────────────────────────┘  │
│                                         │                                   │
│         ┌───────────────────────────────┼───────────────────────────────┐  │
│         │                               │                               │  │
│         ▼                               ▼                               ▼  │
│  ┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐│
│  │    Webhook      │         │   Retry API     │         │   Merchant      ││
│  │    Receiver     │         │   Service       │         │   Dashboard     ││
│  │    Service      │         │                 │         │   (React)       ││
│  │   (Node.js)     │         │   (Node.js)     │         │                 ││
│  └────────┬────────┘         └────────┬────────┘         └────────┬────────┘│
│           │                           │                           │         │
│           │ Events                    │ Read/Write                │ API     │
│           ▼                           ▼                           ▼         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         MESSAGE QUEUE (Redis/SQS)                    │   │
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐            │   │
│  │  │ payment.failed│  │ retry.schedule│  │ retry.execute │            │   │
│  │  │    Queue      │  │    Queue      │  │    Queue      │            │   │
│  │  └───────────────┘  └───────────────┘  └───────────────┘            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│           │                           │                           │         │
│           ▼                           ▼                           ▼         │
│  ┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐│
│  │    Failure      │         │    Retry        │         │    Retry        ││
│  │  Classifier     │────────▶│   Scheduler     │────────▶│   Executor      ││
│  │    Worker       │         │    Worker       │         │    Worker       ││
│  │   (Node.js)     │         │   (Node.js)     │         │   (Node.js)     ││
│  └────────┬────────┘         └────────┬────────┘         └────────┬────────┘│
│           │                           │                           │         │
│           │                           │                           │         │
│           └───────────────────────────┼───────────────────────────┘         │
│                                       │                                     │
│                                       ▼                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                           DATA LAYER                                 │   │
│  │                                                                      │   │
│  │  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐    │   │
│  │  │   PostgreSQL    │   │     Redis       │   │    BigQuery     │    │   │
│  │  │                 │   │                 │   │                 │    │   │
│  │  │ • payments      │   │ • rate limits   │   │ • analytics     │    │   │
│  │  │ • retry_jobs    │   │ • retry counts  │   │ • audit logs    │    │   │
│  │  │ • merchant_cfg  │   │ • cache         │   │ • dashboards    │    │   │
│  │  │ • audit_log     │   │                 │   │                 │    │   │
│  │  └─────────────────┘   └─────────────────┘   └─────────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        OBSERVABILITY                                 │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │   │
│  │  │  Datadog /  │  │   Sentry    │  │  PagerDuty  │                  │   │
│  │  │ Prometheus  │  │             │  │             │                  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Diagrama de Flujo de Datos

```
┌─────────────┐
│   STRIPE    │
│  Webhook    │
└──────┬──────┘
       │ payment_intent.payment_failed
       ▼
┌──────────────────┐
│ Webhook Receiver │
│    Service       │
│                  │
│ • Verify sig     │
│ • Parse event    │
│ • Emit to queue  │
└────────┬─────────┘
         │
         ▼ payment.failed event
┌──────────────────┐
│    Failure       │
│   Classifier     │
│                  │
│ • Lookup code    │
│ • Classify       │
│ • Check merchant │
│   config         │
└────────┬─────────┘
         │
         │ Is Retriable?
         │
    ┌────┴────┐
    │         │
   YES        NO
    │         │
    ▼         ▼
┌─────────┐  ┌─────────┐
│Schedule │  │  Log &  │
│ Retry   │  │  End    │
│ Job     │  │         │
└────┬────┘  └─────────┘
     │
     ▼
┌──────────────────┐
│  Retry Scheduler │
│                  │
│ • Check rate     │
│   limits         │
│ • Calculate      │
│   delay          │
│ • Create job     │
│   in DB          │
└────────┬─────────┘
         │
         │ At scheduled time
         ▼
┌──────────────────┐
│  Retry Executor  │
│                  │
│ • Verify current │
│   state          │
│ • Call processor │
│   API            │
│ • Update payment │
│   status         │
└────────┬─────────┘
         │
    ┌────┴────┐
    │         │
 SUCCESS    FAILURE
    │         │
    ▼         ▼
┌─────────┐  ┌─────────────┐
│ Notify  │  │ More tries? │
│ Success │  └──────┬──────┘
│ & Close │         │
└─────────┘    ┌────┴────┐
               │         │
              YES        NO
               │         │
               ▼         ▼
          ┌─────────┐ ┌─────────┐
          │Schedule │ │ Notify  │
          │Next Try │ │ Final   │
          └─────────┘ │ Failure │
                      └─────────┘
```

---

## Componentes y Tecnologías

### Servicios Backend (Node.js + TypeScript)

| Componente             | Responsabilidad                            | Tecnología                |
| ---------------------- | ------------------------------------------ | ------------------------- |
| **Webhook Receiver**   | Recibir y validar webhooks de procesadores | Express.js, Stripe SDK    |
| **Failure Classifier** | Clasificar fallos y decidir si reintentar  | Service class, PostgreSQL |
| **Retry Scheduler**    | Programar jobs de retry                    | Bull Queue, Redis         |
| **Retry Executor**     | Ejecutar reintentos con procesadores       | Stripe SDK, axios         |
| **Retry API**          | API REST para configuración                | Express.js, OpenAPI       |
| **Merchant Dashboard** | UI de configuración                        | React, TypeScript         |

### Data Stores

| Store          | Uso                                                  | Justificación                 |
| -------------- | ---------------------------------------------------- | ----------------------------- |
| **PostgreSQL** | Datos transaccionales (payments, retry_jobs, config) | ACID, relaciones, ya en stack |
| **Redis**      | Rate limiting, cache, colas                          | Low latency, TTL nativo       |
| **BigQuery**   | Analytics, audit trail largo plazo                   | Escala, SQL analytics         |

### Infraestructura

| Componente        | Tecnología             | Configuración                      |
| ----------------- | ---------------------- | ---------------------------------- |
| **Compute**       | Kubernetes / ECS       | Auto-scaling basado en queue depth |
| **Message Queue** | Redis (Bull) o AWS SQS | Persistencia, retry automático     |
| **API Gateway**   | Kong / AWS ALB         | Rate limiting, auth                |
| **Secrets**       | AWS Secrets Manager    | API keys de procesadores           |

---

## Modelo de Datos

### Tabla: `payments` (existente - se agregan campos)

```sql
ALTER TABLE payments ADD COLUMN IF NOT EXISTS retry_status VARCHAR(20);
-- Values: NULL, 'pending', 'in_progress', 'recovered', 'exhausted'

ALTER TABLE payments ADD COLUMN IF NOT EXISTS retry_count INT DEFAULT 0;
ALTER TABLE payments ADD COLUMN IF NOT EXISTS last_retry_at TIMESTAMP;
ALTER TABLE payments ADD COLUMN IF NOT EXISTS recovered_via_retry BOOLEAN DEFAULT false;
```

### Tabla: `retry_jobs`

```sql
CREATE TABLE retry_jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  payment_id VARCHAR(255) NOT NULL REFERENCES payments(id),
  merchant_id VARCHAR(255) NOT NULL,
  processor VARCHAR(50) NOT NULL,

  attempt_number INT NOT NULL,
  failure_code VARCHAR(100) NOT NULL,
  failure_type VARCHAR(50) NOT NULL,

  scheduled_at TIMESTAMP NOT NULL,
  executed_at TIMESTAMP,

  status VARCHAR(20) NOT NULL DEFAULT 'pending',
  -- Values: 'pending', 'processing', 'completed', 'failed', 'cancelled'

  result VARCHAR(20),
  result_code VARCHAR(100),

  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),

  UNIQUE(payment_id, attempt_number)
);

CREATE INDEX idx_retry_jobs_scheduled ON retry_jobs(scheduled_at)
  WHERE status = 'pending';
CREATE INDEX idx_retry_jobs_payment ON retry_jobs(payment_id);
```

### Tabla: `merchant_retry_config`

```sql
CREATE TABLE merchant_retry_config (
  merchant_id VARCHAR(255) PRIMARY KEY,

  retry_enabled BOOLEAN DEFAULT true,
  max_attempts INT DEFAULT 3 CHECK (max_attempts BETWEEN 1 AND 5),

  -- Configuración por tipo de fallo (JSON para flexibilidad)
  failure_config JSONB DEFAULT '{
    "insufficient_funds": {"enabled": true, "delay_minutes": 1440},
    "card_declined": {"enabled": true, "delay_minutes": 60},
    "network_timeout": {"enabled": true, "delay_minutes": 0},
    "processor_downtime": {"enabled": true, "delay_minutes": 30}
  }',

  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

### Tabla: `failure_code_mapping`

```sql
CREATE TABLE failure_code_mapping (
  id SERIAL PRIMARY KEY,
  processor VARCHAR(50) NOT NULL,
  error_code VARCHAR(100) NOT NULL,

  failure_type VARCHAR(50) NOT NULL,
  is_retriable BOOLEAN NOT NULL,
  recommended_delay_minutes INT,

  description TEXT,

  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),

  UNIQUE(processor, error_code)
);

-- Seed data para Stripe
INSERT INTO failure_code_mapping (processor, error_code, failure_type, is_retriable, recommended_delay_minutes) VALUES
('stripe', 'insufficient_funds', 'insufficient_funds', true, 1440),
('stripe', 'card_declined', 'card_declined', true, 60),
('stripe', 'processing_error', 'network_timeout', true, 0),
('stripe', 'card_velocity_exceeded', 'rate_limited', true, 1440),
('stripe', 'lost_card', 'fraud', false, NULL),
('stripe', 'stolen_card', 'fraud', false, NULL),
('stripe', 'expired_card', 'expired', false, NULL),
('stripe', 'fraudulent', 'fraud', false, NULL);
```

### Tabla: `retry_audit_log`

```sql
CREATE TABLE retry_audit_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  event_type VARCHAR(50) NOT NULL,
  -- Values: 'classified', 'scheduled', 'executed', 'rate_limited', 'recovered', 'exhausted'

  payment_id VARCHAR(255) NOT NULL,
  merchant_id VARCHAR(255) NOT NULL,
  processor VARCHAR(50) NOT NULL,

  attempt_number INT,
  failure_code VARCHAR(100),
  failure_type VARCHAR(50),

  result VARCHAR(20),
  result_code VARCHAR(100),

  card_last4 VARCHAR(4),
  amount_cents BIGINT,
  currency VARCHAR(3),

  metadata JSONB,

  created_at TIMESTAMP DEFAULT NOW()
);

-- Particionado por mes para performance
CREATE INDEX idx_audit_log_created ON retry_audit_log(created_at);
CREATE INDEX idx_audit_log_payment ON retry_audit_log(payment_id);
CREATE INDEX idx_audit_log_merchant ON retry_audit_log(merchant_id, created_at);
```

---

## Diagrama de Secuencia: Retry Flow

```
┌─────────┐  ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌─────────┐  ┌────────┐
│ Stripe  │  │ Webhook  │  │Classifier │  │Scheduler │  │Executor │  │  DB    │
└────┬────┘  └────┬─────┘  └─────┬─────┘  └────┬─────┘  └────┬────┘  └───┬────┘
     │            │              │             │             │           │
     │ payment.failed           │             │             │           │
     │──────────▶│              │             │             │           │
     │            │              │             │             │           │
     │            │ Queue event  │             │             │           │
     │            │─────────────▶│             │             │           │
     │            │              │             │             │           │
     │            │              │ Lookup code │             │           │
     │            │              │─────────────────────────────────────▶│
     │            │              │◀─────────────────────────────────────│
     │            │              │             │             │           │
     │            │              │ Check merchant config     │           │
     │            │              │─────────────────────────────────────▶│
     │            │              │◀─────────────────────────────────────│
     │            │              │             │             │           │
     │            │              │ Is retriable + enabled    │           │
     │            │              │─────────────┤             │           │
     │            │              │             │             │           │
     │            │              │             │ Check rate limit        │
     │            │              │             │────────────────────────▶│
     │            │              │             │◀────────────────────────│
     │            │              │             │             │           │
     │            │              │             │ Create job  │           │
     │            │              │             │─────────────────────────▶│
     │            │              │             │             │           │
     │            │              │             │             │           │
     │            │              │    [After scheduled delay]│           │
     │            │              │             │             │           │
     │            │              │             │ Pick job    │           │
     │            │              │             │◀────────────│           │
     │            │              │             │─────────────▶           │
     │            │              │             │             │           │
     │            │              │             │             │ Verify    │
     │            │              │             │             │ state     │
     │            │              │             │             │──────────▶│
     │            │              │             │             │◀──────────│
     │            │              │             │             │           │
     │◀──────────────────────────────────────────────────────│           │
     │ Confirm PaymentIntent    │             │             │           │
     │──────────────────────────────────────────────────────▶│           │
     │            │              │             │             │           │
     │            │              │             │             │ Update    │
     │            │              │             │             │ status    │
     │            │              │             │             │──────────▶│
     │            │              │             │             │           │
```

---

## APIs

### REST API Endpoints

| Method | Endpoint                              | Descripción                        |
| ------ | ------------------------------------- | ---------------------------------- |
| GET    | `/api/v1/merchants/{id}/retry-config` | Obtener configuración actual       |
| PUT    | `/api/v1/merchants/{id}/retry-config` | Actualizar configuración           |
| GET    | `/api/v1/merchants/{id}/retry-stats`  | Estadísticas de retry              |
| GET    | `/api/v1/payments/{id}/retry-history` | Historial de reintentos de un pago |
| POST   | `/webhooks/stripe`                    | Webhook de Stripe                  |

### Ejemplo: GET Retry Config

```json
// GET /api/v1/merchants/mer_abc123/retry-config

{
  "merchant_id": "mer_abc123",
  "retry_enabled": true,
  "max_attempts": 3,
  "failure_config": {
    "insufficient_funds": {
      "enabled": true,
      "delay_minutes": 1440
    },
    "card_declined": {
      "enabled": true,
      "delay_minutes": 60
    },
    "network_timeout": {
      "enabled": true,
      "delay_minutes": 0
    }
  },
  "stats": {
    "total_retried_30d": 1250,
    "recovered_30d": 312,
    "recovery_rate": 0.2496
  }
}
```

---

## Seguridad y Compliance

### PCI-DSS Compliance

| Requerimiento             | Implementación                             |
| ------------------------- | ------------------------------------------ |
| No almacenar PAN completo | Solo card_fingerprint y last4              |
| No almacenar CVV          | Nunca se recibe ni almacena                |
| Encryption at rest        | PostgreSQL con encryption, Redis AUTH      |
| Encryption in transit     | TLS 1.3 en todas las comunicaciones        |
| Audit trail               | Tabla retry_audit_log con retención 7 años |
| Access control            | RBAC, API keys rotadas                     |

### Rate Limiting

```typescript
// Redis key pattern para rate limiting
const key = `retry:count:${cardFingerprint}:${processor}`;

// Incrementar con TTL de 24h
const count = await redis.incr(key);
if (count === 1) {
  await redis.expire(key, 86400); // 24 hours
}

// Check limit
const MAX_RETRIES_PER_DAY = 5;
if (count > MAX_RETRIES_PER_DAY) {
  throw new RateLimitExceeded();
}
```

---

## Escalabilidad

### Bottlenecks Potenciales y Soluciones

| Componente     | Bottleneck              | Solución                           |
| -------------- | ----------------------- | ---------------------------------- |
| Scheduler      | Single point of failure | Leader election, múltiples workers |
| Redis          | Memory limits           | Cluster mode, eviction policies    |
| PostgreSQL     | Write throughput        | Connection pooling, particionado   |
| Processor APIs | Rate limits externos    | Queue con backpressure             |

### Auto-scaling Rules

```yaml
# Kubernetes HPA
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: retry-executor-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: retry-executor
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: External
      external:
        metric:
          name: redis_queue_depth
          selector:
            matchLabels:
              queue: retry-execute
        target:
          type: AverageValue
          averageValue: 100
```
