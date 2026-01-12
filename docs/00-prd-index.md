# PRD: Automatic Payment Retry Logic

## Product Requirements Document

---

### Información del Documento

| Campo            | Valor                                |
| ---------------- | ------------------------------------ |
| **Autor**        | [Tu nombre]                          |
| **Fecha**        | Enero 2026                           |
| **Versión**      | 1.0                                  |
| **Estado**       | Draft                                |
| **Timeline**     | 6 semanas MVP                        |
| **Stakeholders** | CFO, CTO, Risk/Compliance, Merchants |

---

## Índice de Documentos

### Section 1: Problem & MVP Scope

| #   | Documento                                    | Descripción                                            |
| --- | -------------------------------------------- | ------------------------------------------------------ |
| 1   | [Problem Statement](01-problem-statement.md) | Definición del problema, por qué ahora, asunciones     |
| 2   | [MVP Scope](02-mvp-scope.md)                 | IN vs OUT, must-have, nice-to-have, out of scope       |
| 3   | [Key Risks](03-key-risks.md)                 | Riesgos técnicos, negocio, regulatorios y mitigaciones |

### Section 2: Execution Plan

| #   | Documento                                | Descripción                                |
| --- | ---------------------------------------- | ------------------------------------------ |
| 4   | [Backlog](04-backlog.md)                 | Epics, features, prioridades, estimaciones |
| 5   | [Success Metrics](05-success-metrics.md) | Leading y lagging indicators, queries      |
| 6   | [Rollout Plan](06-rollout-plan.md)       | Beta → Gradual → 100%, timeline            |
| 7   | [Architecture](07-architecture.md)       | Diagrama de componentes y tecnologías      |

---

## Resumen Ejecutivo

### El Problema

Novo procesa pagos para comerciantes en LATAM. ~15% de transacciones fallan en el primer intento, y ~40% de esos fallos podrían recuperarse con reintentos automáticos. Actualmente, los comerciantes deben reintentar manualmente, causando fricción y pérdida de revenue estimada en **+$500K USD/mes en GMV**.

### La Solución

Sistema de retry automático inteligente que:

1. **Detecta** pagos fallidos via webhooks
2. **Clasifica** el tipo de fallo (retriable vs non-retriable)
3. **Programa** reintentos según schedule óptimo por tipo de fallo
4. **Ejecuta** reintentos respetando rate limits de procesadores
5. **Notifica** al comerciante del resultado final

### MVP Scope (6 semanas, 1 FTE)

**MUST-HAVE:**

- Retry engine core con scheduler
- Clasificación de fallos
- Integración con Stripe
- Rate limiting por tarjeta
- Audit trail completo (PCI-DSS)
- Toggle ON/OFF por comerciante
- Notificación de resultado final

**OUT OF SCOPE:**

- ML para predicción
- PSE y Nequi (post-MVP)
- Dashboard avanzado
- Notificaciones a cliente final

### Timeline

```
Week 1-2: Foundation (Detection, Classification, Settings)
Week 3-4: Core Engine (Scheduler, Rate Limiter)
Week 5:   Execution (Executor, Audit Trail)
Week 6:   Polish + Beta (5 merchants)
Week 8-9: Limited Rollout (30% merchants)
Week 10:  Full Rollout (100% merchants)
```

### Métricas de Éxito

| Métrica               | Target Week 6 | Target Week 10 |
| --------------------- | ------------- | -------------- |
| Payment Recovery Rate | ≥ 15%         | ≥ 25%          |
| GMV Recovered         | +$50K USD     | +$150K USD/mes |
| Merchant Adoption     | 30%           | 70%            |

### Riesgos Clave

| Riesgo                       | Mitigación                                           |
| ---------------------------- | ---------------------------------------------------- |
| Rate limit violations        | Contador por tarjeta con TTL, circuit breaker        |
| Retry de pagos non-retriable | Whitelist explícita de códigos, default NO retry     |
| ROI negativo                 | Dashboard de costo vs recovery, threshold automático |
| PCI-DSS                      | No loguear datos sensibles, audit trail completo     |

### Stack Tecnológico

- **Backend**: Node.js microservices (existente)
- **Database**: PostgreSQL (datos) + Redis (rate limits, queues)
- **Analytics**: BigQuery
- **Queue**: Bull (Redis) o AWS SQS
- **Procesadores**: Stripe (MVP), PSE, Nequi (post-MVP)

---

## Cómo usar este PRD

1. **Para entender el problema**: Leer [01-problem-statement.md](01-problem-statement.md)
2. **Para ver qué se va a construir**: Leer [02-mvp-scope.md](02-mvp-scope.md)
3. **Para planificar sprints**: Usar [04-backlog.md](04-backlog.md)
4. **Para definir OKRs**: Consultar [05-success-metrics.md](05-success-metrics.md)
5. **Para diseño técnico**: Revisar [07-architecture.md](07-architecture.md)

---

## Aprobaciones

| Stakeholder     | Estado  | Fecha | Comentarios |
| --------------- | ------- | ----- | ----------- |
| Product         | Pending | -     | -           |
| Engineering     | Pending | -     | -           |
| Risk/Compliance | Pending | -     | -           |
| Finance         | Pending | -     | -           |
