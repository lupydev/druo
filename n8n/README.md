# n8n Payment Retry Workflow

## 🏗️ Arquitectura: Python Backend + n8n Orquestación

**Toda la lógica de negocio está en Python (FastAPI)**. n8n solo orquesta el flujo visual:

```
┌─────────────────────────────────────────────────────────────────────┐
│                          n8n Workflow                               │
├─────────────────────────────────────────────────────────────────────┤
│  [Webhook]  →  [HTTP: classify]  →  [IF: retry?]  →  [Wait]        │
│                                          │                          │
│                     ┌────────────────────┘                          │
│                     ▼                                               │
│              [HTTP: execute]  →  [HTTP: update]  →  [IF: continue?]│
│                     ▲                                    │          │
│                     └────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend (Python)                       │
├─────────────────────────────────────────────────────────────────────┤
│  POST /api/v1/retry-logic/classify     → Clasifica tipo de fallo   │
│  POST /api/v1/retry-logic/execute      → Simula retry (random)     │
│  POST /api/v1/retry-logic/update-status → Actualiza DB + audit     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Importar el Workflow

1. Abre n8n en http://localhost:5678
2. Login con `admin` / `admin123`
3. Click en **"Add workflow"** (botón + arriba a la izquierda)
4. Click en **"Import from File"**
5. Selecciona el archivo `n8n/payment-retry-workflow.json`
6. **Activa el workflow** (toggle arriba a la derecha)

---

## 📦 Endpoints Python que n8n Llama

### `POST /api/v1/retry-logic/classify`

Clasifica el tipo de fallo y verifica si es retriable según la configuración del merchant.

**Request:**

```json
{
  "payment_id": "pay_test_001",
  "failure_type": "network_timeout",
  "merchant_id": "merch_001"
}
```

**Response:**

```json
{
  "payment_id": "pay_test_001",
  "failure_type": "network_timeout",
  "is_retriable": true,
  "retry_enabled": true,
  "max_attempts": 3,
  "delay_minutes": 5,
  "reason": "Eligible for retry"
}
```

---

### `POST /api/v1/retry-logic/execute`

Simula el retry con el procesador de pagos. Usa tasas de éxito basadas en el tipo de fallo.

**Request:**

```json
{
  "payment_id": "pay_test_001",
  "merchant_id": "merch_001",
  "attempt_number": 1,
  "failure_type": "network_timeout"
}
```

**Response:**

```json
{
  "payment_id": "pay_test_001",
  "attempt_number": 1,
  "success": true,
  "result_code": "succeeded",
  "result_message": "Payment recovered successfully",
  "should_continue": false,
  "next_attempt": null
}
```

---

### `POST /api/v1/retry-logic/update-status`

Actualiza el estado del pago en la base de datos y crea un registro de auditoría.

**Request:**

```json
{
  "payment_id": "pay_test_001",
  "attempt_number": 1,
  "success": true,
  "result_code": "succeeded",
  "result_message": "Payment recovered"
}
```

---

## 📊 Tasas de Éxito por Tipo de Fallo

Definidas en Python (`retry_logic.py`):

| Tipo de Fallo        | Tasa de Éxito | Descripción                      |
| -------------------- | ------------- | -------------------------------- |
| `network_timeout`    | 60%           | Problemas temporales de red      |
| `processor_downtime` | 80%           | Procesador caído momentáneamente |
| `insufficient_funds` | 20%           | Usuario sin fondos               |
| `card_declined`      | 15%           | Tarjeta rechazada genérica       |
| `unknown`            | 10%           | Error desconocido                |
| `fraud` / `expired`  | 0%            | No retriable                     |

---

## 🧪 Probar el Flujo Completo

### Opción 1: Usar endpoint de simulación (recomendado)

```bash
curl -X POST http://localhost:8000/api/v1/simulation/trigger-failure \
  -H "Content-Type: application/json" \
  -d '{
    "merchant_id": "11111111-1111-1111-1111-111111111111",
    "amount_cents": 15000,
    "failure_type": "network_timeout"
  }'
```

### Opción 2: Llamar directamente al webhook de n8n

```bash
curl -X POST http://localhost:5678/webhook/payment-failed \
  -H "Content-Type: application/json" \
  -d '{
    "payment_id": "pay_test_001",
    "merchant_id": "11111111-1111-1111-1111-111111111111",
    "failure_type": "network_timeout"
  }'
```

---

## 🎬 Escenarios para Demo

### Escenario 1: Network Timeout (Alta probabilidad)

```bash
# 60% de éxito - probablemente se recupere en 1-2 intentos
curl -X POST http://localhost:5678/webhook/payment-failed \
  -d '{"payment_id": "demo_1", "merchant_id": "11111111-1111-1111-1111-111111111111", "failure_type": "network_timeout"}'
```

### Escenario 2: Insufficient Funds (Baja probabilidad)

```bash
# 20% de éxito - puede agotar los 3 intentos
curl -X POST http://localhost:5678/webhook/payment-failed \
  -d '{"payment_id": "demo_2", "merchant_id": "11111111-1111-1111-1111-111111111111", "failure_type": "insufficient_funds"}'
```

### Escenario 3: Fraud (Non-retriable)

```bash
# 0% - marcado inmediatamente como non-retriable
curl -X POST http://localhost:5678/webhook/payment-failed \
  -d '{"payment_id": "demo_3", "merchant_id": "11111111-1111-1111-1111-111111111111", "failure_type": "fraud"}'
```

---

## 🔍 Ver Resultados

### En n8n

1. Click en "Executions" en el menú lateral
2. Ver cada ejecución con el detalle de cada nodo

### En Backend

```bash
docker-compose logs -f backend
```

### En Base de Datos

```bash
# Ver pagos
docker-compose exec db psql -U postgres -d payments -c "SELECT id, status, failure_type FROM payments;"

# Ver audit logs
docker-compose exec db psql -U postgres -d payments -c "SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 10;"
```

---

## 🛠️ Troubleshooting

### n8n no puede conectar con backend

```bash
# Verificar que backend está corriendo
curl http://localhost:8000/health

# Dentro de Docker, usar nombre del servicio
http://backend:8000  # ✓
http://localhost:8000 # ✗ (desde n8n container)
```

### El workflow no se ejecuta

1. Verificar que el workflow está **activado** (toggle verde arriba a la derecha)
2. Revisar que el webhook path es `payment-failed`
3. Ver logs: `docker-compose logs n8n`

### Los retries no funcionan

1. Verificar que el merchant tiene retry habilitado en la DB
2. Revisar que el failure_type es retriable (no fraud/expired)
3. Ver logs del backend para errores
