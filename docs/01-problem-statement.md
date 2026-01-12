# Problem Statement: Automatic Payment Retry Logic

## 1. ¿Qué estamos resolviendo?

### El Problema

Novo procesa pagos para comerciantes en LATAM. Actualmente, cuando un pago falla (fondos insuficientes, tarjeta rechazada, timeout de red), el sistema lo marca como "fallido" y el comerciante debe reintentar manualmente.

### Impacto Cuantificado

| Métrica                                  | Valor                 | Impacto                               |
| ---------------------------------------- | --------------------- | ------------------------------------- |
| Tasa de fallo en primer intento          | ~15%                  | Fricción para comerciantes y clientes |
| Fallos recuperables con retry automático | ~40%                  | Oportunidad perdida                   |
| Ingresos potenciales perdidos            | +$500K USD/mes en GMV | Revenue leakage significativo         |

### El Costo de No Actuar

- **Comerciantes**: Pierden ventas y deben gestionar manualmente reintentos
- **Clientes finales**: Experiencia de pago frustrante
- **Novo**: $6M USD/año en GMV potencial no capturado
- **Operaciones**: Carga manual en soporte y reconciliación

---

## 2. ¿Por qué ahora?

### Factores de Urgencia

1. **Revenue Impact**: $500K USD/mes representa una oportunidad significativa de crecimiento sin adquirir nuevos comerciantes
2. **Competencia**: Los procesadores de pago modernos ofrecen retry automático como feature estándar
3. **Escala**: A medida que crece el volumen de transacciones, el problema se amplifica proporcionalmente
4. **Viabilidad Técnica**: Ya tenemos los datos de fallos categorizados y la infraestructura base

### Datos de Fallos por Tipo

| Tipo de Fallo                | % del Total | ¿Debe Reintentarse? | Tasa de Éxito en Retry |
| ---------------------------- | ----------- | ------------------- | ---------------------- |
| Fondos insuficientes         | 35%         | Sí, con delay       | 20%                    |
| Tarjeta rechazada (genérico) | 25%         | Sí, limitado        | 15%                    |
| Timeout de red               | 20%         | Sí, inmediato       | 60%                    |
| Procesador caído             | 5%          | Sí, con delay       | 80%                    |
| Otros (tarjeta robada, etc.) | 15%         | NO                  | 0%                     |

### Cálculo de Impacto Esperado

```
Transacciones mensuales fallidas: X
Fallos recuperables (40%): 0.4X
Tasa de recuperación ponderada: ~25% (promedio ponderado por tipo)
Transacciones recuperadas: 0.4X * 0.25 = 0.1X (10% de fallos originales)
```

---

## 3. Asunciones Clave

### Sobre Comportamiento de Usuario

| Asunción                                                     | Validación Requerida               |
| ------------------------------------------------------------ | ---------------------------------- |
| Los comerciantes desean control sobre configuración de retry | Entrevistas con 5 comerciantes top |
| Los clientes aceptan múltiples intentos si son transparentes | Análisis de tickets de soporte     |
| Los comerciantes prefieren retry automático vs manual        | Encuesta rápida                    |

### Sobre Tecnología

| Asunción                                                               | Validación Requerida            |
| ---------------------------------------------------------------------- | ------------------------------- |
| La infraestructura actual soporta jobs programados                     | Review con equipo de plataforma |
| Los procesadores permiten reintentos dentro de sus límites             | Documentación de APIs revisada  |
| Podemos identificar el tipo de fallo desde la respuesta del procesador | Análisis de logs existentes     |

### Sobre Mercado/Negocio

| Asunción                                                         | Validación Requerida                |
| ---------------------------------------------------------------- | ----------------------------------- |
| Los procesadores no penalizarán por reintentos dentro de límites | Confirmar con account managers      |
| El costo de reintentos es menor que el valor recuperado          | Análisis financiero pre-lanzamiento |
| Cumplimos con regulaciones locales de cada país LATAM            | Review con equipo legal             |

---

## 4. Stakeholders y Sus Necesidades

| Stakeholder         | Necesidad Principal                                 | Cómo lo Abordamos                                  |
| ------------------- | --------------------------------------------------- | -------------------------------------------------- |
| **CFO**             | Maximizar conversión de pagos, ROI claro            | Métricas de recovery rate y GMV recuperado         |
| **CTO/Engineering** | Minimizar complejidad, respetar rate limits         | Arquitectura modular, configuración por procesador |
| **Risk/Compliance** | PCI-DSS, no reintentar indefinidamente, audit trail | Límites configurables, logging completo            |
| **Merchants**       | Control sobre comportamiento, visibilidad           | Dashboard de configuración y reportes              |

---

## 5. Definición de Éxito del MVP

### Éxito Mínimo (Week 6)

- [ ] Sistema de retry automático funcionando para al menos 1 procesador (Stripe)
- [ ] Dashboard básico para configuración de retry por comerciante
- [ ] Logging completo de todos los intentos
- [ ] Al menos 10% de fallos recuperables siendo reintentados automáticamente

### Éxito Ideal (Week 10)

- [ ] Soporte para los 3 procesadores principales (Stripe, PSE, Nequi)
- [ ] Tasa de recuperación > 20% en fallos elegibles
- [ ] Adopción por 50%+ de comerciantes activos
- [ ] Impacto medible en GMV (+$100K USD/mes mínimo)
