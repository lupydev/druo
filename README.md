# 🔄 Sistema Automático de Reintentos de Pagos

> **Prueba Técnica para DRUO/Novo** - MVP de lógica automática de reintentos para pagos fallidos

[![PRD](https://img.shields.io/badge/PRD-Completo-green)](./docs/)
[![Backend](https://img.shields.io/badge/Backend-FastAPI-blue)](./back/)
[![Frontend](https://img.shields.io/badge/Frontend-React-61dafb)](./front/)
[![Workflow](https://img.shields.io/badge/Workflow-n8n-orange)](./n8n/)

---

## 📋 Tabla de Contenidos

- [El Problema](#-el-problema)
- [La Solución](#-la-solución)
- [Arquitectura y Enfoque](#-arquitectura-y-enfoque)
- [Inicio Rápido](#-inicio-rápido)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Stack Tecnológico](#-stack-tecnológico)
- [Qué Mejoraría](#-qué-mejoraría)
- [Herramientas de IA Utilizadas](#-herramientas-de-ia-utilizadas)

---

## 🎯 El Problema

### Estado Actual

Novo procesa pagos para comercios en toda LATAM. Cuando un pago falla, el sistema lo marca como "fallido" y los comercios deben **reintentar manualmente** — creando fricción y perdiendo ingresos.

```
┌─────────────────────────────────────────────────────────────────┐
│                        FLUJO ACTUAL                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Cliente ──▶ Pago ──▶ FALLA ──▶ Comercio reintenta manualmente │
│                                              │                   │
│                                              ▼                   │
│                                  😤 Fricción + Ingresos Perdidos │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Los Números

| Métrica                         | Valor          | Impacto                                |
| ------------------------------- | -------------- | -------------------------------------- |
| Tasa de fallo en primer intento | **~15%**       | Alto volumen de transacciones fallidas |
| Fallos recuperables             | **~40%**       | Oportunidad de recuperación automática |
| GMV mensual potencial           | **+$500K USD** | Ingresos que se dejan sobre la mesa    |

### Por Qué Importa

- 💸 **Ingresos Perdidos**: Pagos recuperables no se están recuperando
- 😤 **Fricción para Comercios**: Reintentos manuales consumen tiempo
- 📉 **Abandono de Clientes**: Pagos fallidos = compras abandonadas
- ⏰ **El Timing Importa**: Algunos fallos tienen éxito si se reintentan en el momento correcto

---

## 💡 La Solución

Un **sistema de reintentos inteligente y automatizado** que:

1. **Clasifica fallos** - Determina si un fallo es reintentable
2. **Aplica delays inteligentes** - Espera el tiempo óptimo según el tipo de fallo
3. **Respeta límites** - Honra los rate limits de procesadores y máximo de intentos
4. **Da control a comercios** - Configurable por tipo de fallo
5. **Mantiene auditoría** - Visibilidad total para cumplimiento

### El Nuevo Flujo

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          NUEVO FLUJO                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   Cliente ──▶ Pago ──▶ FALLA ──▶ Clasificar ──▶ ¿Reintentar?            │
│                                                         │                │
│                                           ┌─────────────┴─────────────┐  │
│                                           ▼                           ▼  │
│                                         [SÍ]                        [NO] │
│                                           │                           │  │
│                                    Esperar delay              Marcar como│
│                                      óptimo                    agotado   │
│                                           │                              │
│                                           ▼                              │
│                                    Reintentar Pago                       │
│                                           │                              │
│                               ┌───────────┴───────────┐                  │
│                               ▼                       ▼                  │
│                           [ÉXITO]                [FALLA]                 │
│                               │                       │                  │
│                          ✅ Recuperado         Loop (máx 3x)             │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🏗 Arquitectura y Enfoque

### Arquitectura de Alto Nivel

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   ┌─────────────┐      ┌─────────────┐      ┌─────────────┐             │
│   │             │      │             │      │             │             │
│   │   Frontend  │─────▶│   Backend   │─────▶│  PostgreSQL │             │
│   │   (React)   │      │  (FastAPI)  │      │             │             │
│   │   :5173     │      │    :8000    │      │    :5432    │             │
│   │             │      │             │      │             │             │
│   └─────────────┘      └──────┬──────┘      └─────────────┘             │
│                               │                                          │
│                               │ Webhook                                  │
│                               ▼                                          │
│                        ┌─────────────┐                                   │
│                        │             │                                   │
│                        │     n8n     │──────┐                            │
│                        │  Workflows  │      │                            │
│                        │    :5678    │      │ HTTP Callbacks             │
│                        │             │      │                            │
│                        └─────────────┘      │                            │
│                                             ▼                            │
│                                    ┌─────────────────┐                   │
│                                    │  Lógica Retry   │                   │
│                                    │    (Python)     │                   │
│                                    │   /classify     │                   │
│                                    │   /execute      │                   │
│                                    │   /update       │                   │
│                                    └─────────────────┘                   │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Decisiones de Diseño

| Decisión             | Elección         | Razón                                                      |
| -------------------- | ---------------- | ---------------------------------------------------------- |
| **Backend**          | FastAPI + Python | Familiar, rápido para iterar, async-first                  |
| **Base de Datos**    | PostgreSQL       | Robusto, soporta queries complejas, production-ready       |
| **Orquestación**     | n8n              | Workflow visual, fácil modificar lógica, maneja scheduling |
| **Frontend**         | React + Vite     | Simple, experiencia de desarrollo rápida                   |
| **Ubicación Lógica** | Endpoints Python | n8n orquesta, Python ejecuta — lo mejor de ambos           |

### ⚠️ Importante: Modo Simulación

> **Este MVP simula los webhooks de procesadores.** No hay integración real con Stripe, PSE, Nequi, etc.

En esta demo:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      QUÉ HACE n8n EN ESTE MVP                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   Mundo Real:                                                            │
│   ───────────                                                            │
│   Stripe ──webhook──▶ Backend ──▶ n8n ──▶ Stripe API (reintento)        │
│                                                                          │
│   Este MVP (Simulación):                                                 │
│   ──────────────────────                                                 │
│   Dashboard ──simular──▶ Backend ──▶ n8n ──▶ Lógica Python (mock retry) │
│                                                    │                     │
│                                                    ▼                     │
│                                            Éxito probabilístico          │
│                                            (60% red, 20% fondos, etc)    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

**Qué está simulado:**

- ❌ No hay llamadas reales a APIs de procesadores de pago
- ❌ No hay webhooks reales de Stripe/PSE/Nequi
- ✅ La lógica de reintentos es real (clasificación, delays, máximo de intentos)
- ✅ El estado de la base de datos es real (pagos, logs de auditoría)
- ✅ La orquestación del workflow es real (scheduling de n8n, callbacks)
- ✅ Éxito/fallo es **probabilístico** basado en el tipo de fallo

**Para integrar con procesadores reales**, se necesitaría:

1. Agregar endpoints de webhook para recibir eventos de pago reales
2. Implementar adaptadores de PSP (Stripe, PSE, Nequi)
3. Reemplazar mock retry con llamadas reales a `PaymentIntent.confirm()`

### ¿Por Qué Este Enfoque?

#### 1. **Separación de Responsabilidades**

```
n8n = Orquestación (cuándo hacer las cosas, scheduling, control de flujo)
Python = Lógica de Negocio (qué hacer, cómo clasificar, probabilidad de éxito)
```

Esto significa:

- ✅ Lógica de reintentos es testeable (unit tests en Python)
- ✅ Workflow es visible (UI de n8n muestra ejecución)
- ✅ Fácil de modificar (cambiar delays sin cambios de código)

#### 2. **Control del Comercio**

Cada comercio puede configurar:

- Activar/desactivar reintentos globalmente
- Activar/desactivar por tipo de fallo (network_timeout, insufficient_funds, etc.)
- Establecer máximo de intentos (1-10)
- Establecer delay por tipo de fallo

#### 3. **Agnóstico de Procesador**

El sistema está diseñado para funcionar con **cualquier procesador de pago**:

- Stripe, PSE, Nequi, PayPal, etc.
- Cada uno puede tener su propio adaptador (patrón listo)
- Los tipos de fallo se normalizan internamente

#### 4. **Auditoría y Cumplimiento**

Cada acción queda registrada:

- Decisiones de clasificación
- Intentos de reintento
- Resultados de éxito/fallo
- Timestamps para todos los eventos

---

## 🚀 Inicio Rápido

### Prerrequisitos

- **Docker** y **Docker Compose**
- **Node.js 18+** y **Bun** (para frontend)
- **Make** (opcional)

### 1. Iniciar Backend + Base de Datos + n8n

```bash
cd back
make up-build

# O sin Make:
docker-compose up --build -d
```

### 2. Iniciar Frontend

```bash
cd front
bun install
bun run dev
```

### 3. Acceder a los Servicios

| Servicio              | URL                        |
| --------------------- | -------------------------- |
| **Dashboard**         | http://localhost:5173      |
| **Documentación API** | http://localhost:8000/docs |
| **Workflows n8n**     | http://localhost:5678      |

### 4. Probar el Flujo

1. Abrir el Dashboard
2. Click en "Simular Fallo" → Seleccionar un tipo de fallo
3. Ver el pago aparecer en la tabla
4. Ver los reintentos suceder automáticamente (si están habilitados)

---

## 📁 Estructura del Proyecto

```
druo/
├── docs/                          # 📋 Documentación PRD
│   ├── 00-prd-index.md
│   ├── 01-problem-statement.md
│   ├── 02-mvp-scope.md
│   ├── 03-key-risks.md
│   ├── 04-backlog.md
│   ├── 05-success-metrics.md
│   ├── 06-rollout-plan.md
│   └── 07-architecture.md
│
├── back/                          # 🐍 FastAPI Backend
│   ├── app/
│   │   ├── api/v1/endpoints/
│   │   │   ├── payments.py
│   │   │   ├── retry_config.py
│   │   │   ├── retry_logic.py     # Lógica core de reintentos
│   │   │   └── simulation.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   └── seeds.py
│   │   └── models/
│   ├── db/
│   │   └── schema.sql
│   ├── docker-compose.yaml
│   ├── Dockerfile
│   ├── Makefile
│   └── pyproject.toml             # Dependencias uv
│
├── front/                         # ⚛️ Frontend React
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.tsx
│   │   │   ├── StatsGrid.tsx
│   │   │   ├── SimulatePanel.tsx
│   │   │   ├── ConfigPanel.tsx
│   │   │   └── PaymentsTable.tsx
│   │   ├── api.ts
│   │   ├── types.ts
│   │   └── App.tsx
│   └── package.json
│
├── n8n/                           # 🔄 Definiciones de workflow
│   └── payment-retry-workflow.json
│
└── README.md                      # 📖 Estás aquí
```

---

## 🛠 Stack Tecnológico

### Backend

| Tecnología        | Propósito                   |
| ----------------- | --------------------------- |
| **Python 3.13**   | Lenguaje                    |
| **FastAPI**       | Framework de API            |
| **SQLModel**      | ORM (SQLAlchemy + Pydantic) |
| **PostgreSQL 15** | Base de datos               |
| **uv**            | Gestión de dependencias     |
| **Docker**        | Containerización            |

### Frontend

| Tecnología     | Propósito                    |
| -------------- | ---------------------------- |
| **React 19**   | Framework UI                 |
| **TypeScript** | Tipado seguro                |
| **Vite 7**     | Herramienta de build         |
| **Bun**        | Runtime y gestor de paquetes |

### Workflow

| Tecnología     | Propósito                   |
| -------------- | --------------------------- |
| **n8n**        | Orquestación de workflows   |
| **Webhooks**   | Triggers basados en eventos |
| **Nodos HTTP** | Comunicación con API        |

---

## 🔮 Qué Mejoraría

### Con Más Tiempo

1. **Integración Real con PSP**

   - Conectar con sandbox de Stripe
   - Implementar patrón adapter para multi-PSP
   - Verificación real de webhooks

2. **Analíticas Mejoradas**

   - Tendencias de tasa de recuperación en el tiempo
   - Calculadora de ahorros
   - Dashboards por comercio

3. **Estrategias de Reintento Avanzadas**

   - Backoff exponencial
   - Jitter para reintentos distribuidos
   - Circuit breaker para procesadores fallando

4. **Hardening para Producción**

   - Redis para cola de trabajos
   - Distributed locking
   - Enforcement de rate limit a nivel gateway

5. **Testing**

   - Unit tests para lógica de reintentos
   - Integration tests para workflows
   - E2E tests para dashboard

6. **Observabilidad**
   - Logging estructurado
   - Métricas (Prometheus)
   - Distributed tracing

---

## 🤖 Herramientas de IA Utilizadas

| Herramienta                 | Cómo Ayudó                                             |
| --------------------------- | ------------------------------------------------------ |
| **GitHub Copilot (Claude)** | Decisiones de arquitectura, generación de código, docs |

### Cómo la IA Aceleró el Desarrollo

1. **Diseño de Arquitectura** - Discutir trade-offs entre diferentes enfoques
2. **Generación de Boilerplate** - Modelos, endpoints, configuración Docker
3. **Resolución de Problemas** - Debugging de issues async, quirks de SQLModel
4. **Documentación** - Generación de README, comentarios inline

---

## 📊 Métricas de Éxito

### Indicadores Adelantados (Durante Desarrollo)

- ✅ Workflow de reintentos ejecuta correctamente
- ✅ Lógica de clasificación es precisa
- ✅ Cambios de configuración aplican inmediatamente

### Indicadores Rezagados (Resultados de Negocio)

- 📈 **Tasa de Recuperación**: % de pagos fallidos recuperados
- 💰 **GMV Recuperado**: Valor en dólares de pagos recuperados
- ⏱️ **Tiempo de Recuperación**: Tiempo promedio desde fallo hasta éxito

---

## 📚 Documentación

PRD detallado disponible en [`/docs`](./docs/):

1. [Índice PRD](./docs/00-prd-index.md)
2. [Planteamiento del Problema](./docs/01-problem-statement.md)
3. [Alcance del MVP](./docs/02-mvp-scope.md)
4. [Riesgos Clave](./docs/03-key-risks.md)
5. [Backlog](./docs/04-backlog.md)
6. [Métricas de Éxito](./docs/05-success-metrics.md)
7. [Plan de Rollout](./docs/06-rollout-plan.md)
8. [Arquitectura](./docs/07-architecture.md)

---

<div align="center">

**Construido con ❤️ para DRUO**

_"Moverse rápido, entregar soluciones que funcionan"_

</div>
