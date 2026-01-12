# Success Metrics: Automatic Payment Retry Logic

## Framework de Métricas

Utilizamos el modelo de métricas Input → Output → Outcome para asegurar que medimos tanto el progreso durante desarrollo como el impacto de negocio.

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   INPUT     │────►│   OUTPUT    │────►│   OUTCOME   │
│  (Leading)  │     │  (Leading)  │     │  (Lagging)  │
├─────────────┤     ├─────────────┤     ├─────────────┤
│ Esfuerzo y  │     │ Funcionalid.│     │ Impacto de  │
│ desarrollo  │     │ entregadas  │     │ negocio     │
└─────────────┘     └─────────────┘     └─────────────┘
```

---

## Métricas Leading (Durante Desarrollo)

### L1: Velocity de Desarrollo

| Aspecto        | Detalle                             |
| -------------- | ----------------------------------- |
| **Definición** | Story points completados por sprint |
| **Target**     | 10-11 SP por sprint (2 semanas)     |
| **Frecuencia** | Semanal                             |
| **Fuente**     | Jira/Linear                         |

**Query/Tracking:**

```sql
-- Si usamos Linear o similar con API
SELECT
  sprint_id,
  SUM(story_points) as completed_points
FROM issues
WHERE status = 'done'
  AND completed_at BETWEEN sprint_start AND sprint_end
GROUP BY sprint_id
```

**Alertas:**

- 🟢 Verde: ≥ 90% del target
- 🟡 Amarillo: 70-89% del target
- 🔴 Rojo: < 70% del target

---

### L2: Test Coverage

| Aspecto        | Detalle                                      |
| -------------- | -------------------------------------------- |
| **Definición** | % de código cubierto por tests automatizados |
| **Target**     | ≥ 80% para código nuevo                      |
| **Frecuencia** | Por PR / Diario                              |
| **Fuente**     | Jest/Coverage reports en CI                  |

**Query/Tracking:**

```bash
# En CI pipeline
npm run test:coverage -- --coverageThreshold='{"global":{"lines":80}}'
```

---

### L3: Retry Jobs Scheduled (Staging)

| Aspecto        | Detalle                                              |
| -------------- | ---------------------------------------------------- |
| **Definición** | Número de retry jobs creados exitosamente en staging |
| **Target**     | 100% de pagos fallidos retriable generan job         |
| **Frecuencia** | Continuo en staging                                  |
| **Fuente**     | Logs/Metrics de staging                              |

**Query:**

```sql
SELECT
  DATE(created_at) as date,
  COUNT(*) as jobs_scheduled,
  COUNT(DISTINCT payment_id) as unique_payments
FROM retry_jobs
WHERE environment = 'staging'
GROUP BY DATE(created_at)
```

---

### L4: Tiempo de Procesamiento de Job

| Aspecto        | Detalle                                   |
| -------------- | ----------------------------------------- |
| **Definición** | Latencia entre scheduled_at y executed_at |
| **Target**     | p95 < 30 segundos de delay                |
| **Frecuencia** | Continuo                                  |
| **Fuente**     | Datadog/Prometheus                        |

**Query:**

```sql
SELECT
  PERCENTILE_CONT(0.95) WITHIN GROUP (
    ORDER BY EXTRACT(EPOCH FROM (executed_at - scheduled_at))
  ) as p95_seconds
FROM retry_jobs
WHERE executed_at IS NOT NULL
```

---

## Métricas Lagging (Post-Launch)

### B1: Payment Recovery Rate (PRIMARY)

| Aspecto            | Detalle                                                     |
| ------------------ | ----------------------------------------------------------- |
| **Definición**     | % de pagos fallidos retriable que se recuperan exitosamente |
| **Target Week 6**  | ≥ 15%                                                       |
| **Target Week 10** | ≥ 25%                                                       |
| **Frecuencia**     | Diario                                                      |
| **Fuente**         | PostgreSQL + BigQuery                                       |

**Query:**

```sql
WITH retriable_failures AS (
  SELECT payment_id
  FROM payment_failures
  WHERE is_retriable = true
    AND created_at >= '2026-01-01'
),
recovered AS (
  SELECT DISTINCT rf.payment_id
  FROM retriable_failures rf
  JOIN retry_audit_log ral ON rf.payment_id = ral.payment_id
  WHERE ral.result = 'SUCCESS'
)
SELECT
  COUNT(DISTINCT recovered.payment_id)::float /
  COUNT(DISTINCT retriable_failures.payment_id) * 100 as recovery_rate
FROM retriable_failures
LEFT JOIN recovered ON retriable_failures.payment_id = recovered.payment_id
```

**Dashboard Visualization:**

- Gráfico de línea: Recovery rate por día
- Breakdown por tipo de fallo
- Comparación: antes vs después del lanzamiento

---

### B2: GMV Recovered (PRIMARY)

| Aspecto            | Detalle                                                   |
| ------------------ | --------------------------------------------------------- |
| **Definición**     | Valor monetario de pagos recuperados via retry automático |
| **Target Week 6**  | +$50K USD                                                 |
| **Target Week 10** | +$150K USD/mes                                            |
| **Frecuencia**     | Diario, reporte semanal                                   |
| **Fuente**         | BigQuery                                                  |

**Query:**

```sql
SELECT
  DATE(recovered_at) as date,
  SUM(amount_cents) / 100 as gmv_recovered_usd,
  COUNT(*) as payments_recovered
FROM payments
WHERE status = 'succeeded'
  AND recovered_via_retry = true
  AND recovered_at >= '2026-01-01'
GROUP BY DATE(recovered_at)
ORDER BY date DESC
```

**Cálculo de ROI:**

```
ROI = (GMV Recovered * Margin) / (Retry Costs + Development Cost)

Donde:
- GMV Recovered = Suma de pagos recuperados
- Margin = % que Novo gana por transacción (~2%)
- Retry Costs = Fees de procesador por intentos fallidos
- Development Cost = 6 semanas * 1 FTE (amortizado)
```

---

### B3: Retry Success Rate por Tipo de Fallo

| Aspecto        | Detalle                                                    |
| -------------- | ---------------------------------------------------------- |
| **Definición** | % de éxito en retry, segmentado por tipo de fallo original |
| **Target**     | Dentro de 5% de benchmarks esperados                       |
| **Frecuencia** | Semanal                                                    |
| **Fuente**     | BigQuery                                                   |

**Benchmarks Esperados:**
| Tipo de Fallo | Target Recovery |
|---------------|-----------------|
| Network timeout | 60% |
| Processor downtime | 80% |
| Insufficient funds | 20% |
| Card declined (generic) | 15% |

**Query:**

```sql
SELECT
  failure_type,
  COUNT(CASE WHEN final_result = 'SUCCESS' THEN 1 END) as recovered,
  COUNT(*) as total_retried,
  ROUND(COUNT(CASE WHEN final_result = 'SUCCESS' THEN 1 END)::numeric /
        COUNT(*) * 100, 2) as recovery_rate
FROM retry_audit_log
WHERE attempt_number = (
  SELECT MAX(attempt_number)
  FROM retry_audit_log ral2
  WHERE ral2.payment_id = retry_audit_log.payment_id
)
GROUP BY failure_type
ORDER BY recovery_rate DESC
```

---

### B4: Merchant Adoption Rate

| Aspecto            | Detalle                                                   |
| ------------------ | --------------------------------------------------------- |
| **Definición**     | % de comerciantes activos con retry automático habilitado |
| **Target Week 6**  | ≥ 30% (beta merchants)                                    |
| **Target Week 10** | ≥ 70%                                                     |
| **Frecuencia**     | Semanal                                                   |
| **Fuente**         | PostgreSQL                                                |

**Query:**

```sql
WITH active_merchants AS (
  SELECT DISTINCT merchant_id
  FROM payments
  WHERE created_at >= NOW() - INTERVAL '30 days'
),
retry_enabled AS (
  SELECT merchant_id
  FROM merchant_retry_config
  WHERE retry_enabled = true
)
SELECT
  COUNT(DISTINCT re.merchant_id)::float /
  COUNT(DISTINCT am.merchant_id) * 100 as adoption_rate
FROM active_merchants am
LEFT JOIN retry_enabled re ON am.merchant_id = re.merchant_id
```

---

### B5: Cost per Recovery

| Aspecto        | Detalle                                                     |
| -------------- | ----------------------------------------------------------- |
| **Definición** | Costo promedio en fees de procesador para recuperar un pago |
| **Target**     | < 10% del valor del pago recuperado                         |
| **Frecuencia** | Semanal                                                     |
| **Fuente**     | Billing data + BigQuery                                     |

**Query:**

```sql
WITH recovery_costs AS (
  SELECT
    payment_id,
    SUM(processor_fee_cents) as total_retry_fees,
    MAX(amount_cents) as payment_amount
  FROM retry_audit_log
  WHERE final_result = 'SUCCESS'
  GROUP BY payment_id
)
SELECT
  AVG(total_retry_fees::float / payment_amount * 100) as avg_cost_percentage,
  SUM(total_retry_fees) / 100 as total_fees_usd,
  SUM(payment_amount) / 100 as total_recovered_usd
FROM recovery_costs
```

---

## Dashboard de Métricas

### Vista Ejecutiva (CFO)

```
┌─────────────────────────────────────────────────────────────┐
│                    RETRY PERFORMANCE                         │
├──────────────────────┬──────────────────────────────────────┤
│  GMV Recovered MTD   │  $127,450 USD                        │
│  ████████████░░░░░░  │  Target: $150K ─ 85% achieved        │
├──────────────────────┼──────────────────────────────────────┤
│  Recovery Rate       │  23.5%                               │
│  ███████████████░░░  │  Target: 25% ─ 94% achieved          │
├──────────────────────┼──────────────────────────────────────┤
│  ROI                 │  3.2x                                │
│  Fees: $3,200        │  Revenue: $10,240                    │
└──────────────────────┴──────────────────────────────────────┘
```

### Vista Operativa (Engineering)

```
┌─────────────────────────────────────────────────────────────┐
│                  SYSTEM HEALTH                               │
├───────────────┬───────────────┬───────────────┬─────────────┤
│ Jobs Pending  │ Jobs/min      │ P95 Latency   │ Error Rate  │
│     234       │     45        │    12s        │   0.02%     │
├───────────────┴───────────────┴───────────────┴─────────────┤
│                                                             │
│  Scheduler Heartbeat: ✅ Healthy (last: 12s ago)           │
│  Rate Limit Hits: 23 (last 24h) ⚠️                         │
│  Unclassified Errors: 2 ⚠️ (need mapping)                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Eventos a Trackear

Para alimentar las métricas, necesitamos trackear estos eventos:

| Evento                   | Trigger                  | Propiedades                                               |
| ------------------------ | ------------------------ | --------------------------------------------------------- |
| `payment.failed`         | Webhook recibido         | payment_id, failure_code, amount, merchant_id             |
| `payment.classified`     | Después de clasificación | payment_id, is_retriable, failure_type, recommended_delay |
| `retry.scheduled`        | Job creado               | payment_id, attempt_number, scheduled_at                  |
| `retry.executed`         | Job ejecutado            | payment_id, attempt_number, result, processor_response    |
| `retry.rate_limited`     | Límite alcanzado         | payment_id, card_fingerprint, current_count               |
| `payment.recovered`      | Retry exitoso            | payment_id, total_attempts, recovered_amount              |
| `retry.exhausted`        | Todos intentos fallidos  | payment_id, total_attempts, final_failure_code            |
| `merchant.retry_toggled` | Config cambiada          | merchant_id, new_value, previous_value                    |

---

## Alertas Configuradas

| Métrica             | Threshold               | Severidad | Canal     |
| ------------------- | ----------------------- | --------- | --------- |
| Scheduler heartbeat | > 5 min sin heartbeat   | P1        | PagerDuty |
| Error rate          | > 5%                    | P1        | PagerDuty |
| Recovery rate drop  | < 10% (cuando era >20%) | P2        | Slack     |
| Rate limit hits     | > 100/hora              | P2        | Slack     |
| Unclassified errors | > 0                     | P3        | Slack     |
| Job queue depth     | > 10,000                | P2        | Slack     |
