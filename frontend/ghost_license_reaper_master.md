# 👻 Ghost License Reaper: Master Manual

Este documento es la fuente de verdad definitiva para el proyecto **Ghost License Reaper**, un SaaS diseñado para detectar y eliminar el desperdicio en suscripciones de software.

## 🚀 Visión General
Ghost License Reaper ayuda a las empresas a ahorrar miles de dólares al mes identificando licencias SaaS no utilizadas mediante el escaneo de facturas en Gmail y el análisis de actividad en SSO.

## 🏗️ Arquitectura Técnica

### Backend (Supabase)
- **Base de Datos**: PostgreSQL con RLS (Row Level Security) activo.
  - `invoices`: Tabla principal que almacena datos de facturas extraídos.
  - `user_profiles`: Datos extendidos del usuario y vinculación con empresas.
  - `onboarding_progress`: Seguimiento del flujo de configuración inicial.
  - `invoice_summary`: Vista SQL para reportes agregados por vendedor.
- **Edge Functions** (TypeScript/Deno):
  - `scan-invoices`: Conector con la API de Gmail. Usa regex avanzados para extraer montos, fechas y proveedores.
  - `create-checkout-session`: Integración con Stripe para gestionar suscripciones.

### Frontend (Vanilla JS + Vite)
- **Dashboard**: Interfaz dinámica que muestra el "Total Wasted" y la "Kill List".
- **Calculadora**: Herramienta de marketing para leads basada en benchmarks de la industria.
- **Onboarding**: Flujo de 3 pasos (Empresa -> Integración -> Primer Escaneo).

## 🛠️ Implementaciones Clave

### 1. Sistema de Pagos (Stripe)
- Botón "Upgrade to Pro" integrado en el Dashboard.
- Módulo `src/lib/stripe.js` configurado para manejar sesiones de checkout.
- Infraestructura preparada para suscripciones STARTER, PRO y ENTERPRISE.

### 2. Onboarding 100% Funcional
- Flujo completo desde el registro hasta el primer escaneo real.
- Conexión directa con la Edge Function de Gmail en el paso final.
- Interfaz premium con micro-animaciones y barras de progreso.

### 3. Inteligencia de Extracción
- Sistema de detección de proveedores SaaS basado en patrones de remitente y asunto.
- Extracción automática de moneda (USD, EUR, GBP, etc.) y fechas de renovación.

## 📋 Lo que queda (Roadmap)
- [ ] **Acción de Cancelación**: Implementar la lógica del botón "Reap" para procesar bajas.
- [ ] **OAuth Completo**: Finalizar la interfaz de conexión de Google dentro de Settings.
- [ ] **IDs de Produccion**: Reemplazar los IDs de prueba de Stripe por los definitivos.

---
*Este manual se actualiza automáticamente con cada mejora del sistema.*
