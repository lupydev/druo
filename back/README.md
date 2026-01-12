# 🔄 Payment Retry System - Backend

Sistema automático de reintentos de pagos fallidos. MVP desarrollado con FastAPI, PostgreSQL y n8n.

![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.128-green?logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue?logo=postgresql)
![Docker](https://img.shields.io/badge/Docker-Compose-blue?logo=docker)
![n8n](https://img.shields.io/badge/n8n-Workflow-orange)

---

## 📋 Tabla de Contenidos

- [Arquitectura](#-arquitectura)
- [Quick Start](#-quick-start)
- [Comandos Útiles](#-comandos-útiles)
- [API Endpoints](#-api-endpoints)
- [Configuración de Reintentos](#-configuración-de-reintentos)
- [Desarrollo Local](#-desarrollo-local)
- [Estructura del Proyecto](#-estructura-del-proyecto)

---

## 🏗 Arquitectura

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│    Frontend     │────▶│  FastAPI API    │────▶│   PostgreSQL    │
│   (React/Vite)  │     │    :8000        │     │     :5432       │
│                 │     │                 │     │                 │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                                 │ Webhook
                                 ▼
                        ┌─────────────────┐
                        │                 │
                        │      n8n        │
                        │   Workflows     │
                        │     :5678       │
                        │                 │
                        └────────┬────────┘
                                 │
                                 │ HTTP Callbacks
                                 ▼
                        ┌─────────────────┐
                        │  Retry Logic    │
                        │  (Python)       │
                        └─────────────────┘
```

---

## 🚀 Quick Start

### Prerrequisitos

- **Docker** y **Docker Compose**
- **uv** (gestor de dependencias Python) - [Instalar](https://docs.astral.sh/uv/)
- **Make** (opcional, para comandos simplificados)

### 1. Levantar el proyecto

```bash
# Clonar e ir al directorio backend
cd back

# Levantar todos los servicios (PostgreSQL, Backend, n8n)
make up-build

# O sin Make:
docker-compose up --build -d
```

### 2. Verificar que todo funciona

```bash
# Ver URLs de los servicios
make urls

# Verificar health del API
make health
# Respuesta: {"status": "healthy", ...}
```

### 3. Acceder a los servicios

| Servicio       | URL                        | Credenciales            |
| -------------- | -------------------------- | ----------------------- |
| **API Docs**   | http://localhost:8000/docs | -                       |
| **n8n**        | http://localhost:5678      | `admin` / `admin123`    |
| **PostgreSQL** | localhost:5432             | `postgres` / `postgres` |

### 4. Probar el flujo de reintentos

```bash
# Simular un pago fallido
make simulate

# Ver estadísticas
make stats

# Ver pagos
make payments
```

---

## 🛠 Comandos Útiles

### Docker

| Comando             | Descripción                                   |
| ------------------- | --------------------------------------------- |
| `make up`           | Levantar servicios                            |
| `make up-build`     | Levantar con rebuild                          |
| `make down`         | Detener servicios                             |
| `make clean`        | Detener y eliminar volúmenes (⚠️ borra datos) |
| `make logs`         | Ver logs de todos los servicios               |
| `make logs-backend` | Ver solo logs del backend                     |
| `make restart`      | Reiniciar backend                             |

### Desarrollo

| Comando         | Descripción                        |
| --------------- | ---------------------------------- |
| `make shell`    | Acceder a shell del backend        |
| `make db-shell` | Acceder a PostgreSQL               |
| `make urls`     | Mostrar URLs de servicios          |
| `make help`     | Ver todos los comandos disponibles |

### Demo & Testing

| Comando                 | Descripción                                |
| ----------------------- | ------------------------------------------ |
| `make health`           | Verificar health del API                   |
| `make simulate`         | Simular fallo: insufficient_funds          |
| `make simulate-network` | Simular fallo: network_timeout (60% éxito) |
| `make simulate-fraud`   | Simular fallo: fraud (no retriable)        |
| `make stats`            | Ver estadísticas de reintentos             |
| `make payments`         | Listar pagos                               |
| `make enable-retry`     | Activar reintentos                         |
| `make disable-retry`    | Desactivar reintentos                      |

---

## 📡 API Endpoints

### Pagos

```
GET  /api/v1/payments/                    # Listar pagos
GET  /api/v1/payments/{payment_id}        # Obtener pago
```

### Configuración de Reintentos

```
GET  /api/v1/retry-config/{merchant_id}          # Obtener config
PUT  /api/v1/retry-config/{merchant_id}          # Actualizar config
GET  /api/v1/retry-config/{merchant_id}/preview  # Preview de config
```

### Simulación (Demo)

```
POST /api/v1/simulate/failure             # Simular fallo de pago
GET  /api/v1/simulate/stats/{merchant_id} # Estadísticas
```

### Retry Logic (llamados por n8n)

```
POST /api/v1/retry-logic/classify         # Clasificar fallo
POST /api/v1/retry-logic/execute          # Ejecutar reintento
POST /api/v1/retry-logic/update-status    # Actualizar estado
```

### Health

```
GET  /health                              # Health check
```

📖 **Documentación interactiva**: http://localhost:8000/docs

---

## ⚙️ Configuración de Reintentos

Cada merchant puede configurar:

| Campo                        | Descripción                     | Default      |
| ---------------------------- | ------------------------------- | ------------ |
| `retry_enabled`              | Activar/desactivar reintentos   | `true`       |
| `max_attempts`               | Máximo de reintentos            | `3`          |
| `insufficient_funds_enabled` | Reintentar fondos insuficientes | `true`       |
| `insufficient_funds_delay`   | Delay en minutos                | `1440` (24h) |
| `card_declined_enabled`      | Reintentar tarjeta rechazada    | `true`       |
| `card_declined_delay`        | Delay en minutos                | `60` (1h)    |
| `network_timeout_enabled`    | Reintentar timeout de red       | `true`       |
| `network_timeout_delay`      | Delay en minutos                | `5`          |

### Probabilidades de Éxito (Simulación)

| Tipo de Fallo        | Probabilidad      |
| -------------------- | ----------------- |
| `network_timeout`    | 60%               |
| `processor_downtime` | 80%               |
| `insufficient_funds` | 20%               |
| `card_declined`      | 15%               |
| `fraud`              | 0% (no retriable) |
| `expired`            | 0% (no retriable) |

---

## 💻 Desarrollo Local

### Con uv (recomendado)

```bash
# Instalar dependencias
uv sync

# Activar entorno virtual
source .venv/bin/activate

# Correr servidor de desarrollo
fastapi dev app/main.py --host 0.0.0.0
```

### Variables de Entorno

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/retry_db
N8N_WEBHOOK_URL=http://localhost:5678/webhook
ENVIRONMENT=development
```

### Seeds

Los datos iniciales se aplican automáticamente al iniciar el backend:

- **Demo Merchant**: `466fd34b-96a1-4635-9b2c-dedd2645291f`
- **Configuración por defecto**
- **Pagos de prueba** (solo en development)

---

## 📁 Estructura del Proyecto

```
back/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── payments.py       # CRUD de pagos
│   │       │   ├── retry_config.py   # Configuración
│   │       │   ├── retry_logic.py    # Lógica de reintentos
│   │       │   └── simulation.py     # Simulación demo
│   │       └── router.py
│   ├── core/
│   │   ├── config.py                 # Settings
│   │   ├── database.py               # Conexión DB
│   │   └── seeds.py                  # Datos iniciales
│   ├── models/
│   │   ├── merchant.py
│   │   ├── payment.py
│   │   ├── retry_config.py
│   │   ├── retry_job.py
│   │   └── audit_log.py
│   ├── services/
│   │   └── n8n_service.py            # Cliente n8n
│   └── main.py                       # Entry point
├── db/
│   └── schema.sql                    # DDL
├── docker-compose.yaml
├── Dockerfile
├── entrypoint.sh
├── Makefile
├── pyproject.toml
└── uv.lock
```

---

## 🔧 Configurar n8n

1. Acceder a http://localhost:5678
2. Importar el workflow desde `/n8n/payment-retry-workflow.json`
3. Activar el workflow

El workflow:

1. Recibe webhook de pago fallido
2. Llama a `/retry-logic/classify` para clasificar
3. Espera el delay configurado
4. Llama a `/retry-logic/execute` para reintentar
5. Actualiza el estado del pago

---

## 📊 Demo Merchant ID

Para pruebas, usa este ID:

```
466fd34b-96a1-4635-9b2c-dedd2645291f
```

---

## 🐛 Troubleshooting

### El backend no conecta a la DB

```bash
# Verificar que PostgreSQL está corriendo
docker-compose ps

# Ver logs de la DB
docker-compose logs db

# Recrear todo limpio
make clean && make up-build
```

### n8n no recibe webhooks

```bash
# Verificar logs de n8n
make logs-n8n

# Probar webhook directamente
make test-n8n
```

### Reiniciar todo desde cero

```bash
make clean      # Elimina contenedores y volúmenes
make up-build   # Reconstruye todo
```

---

**Desarrollado con ❤️ para DRUO**
