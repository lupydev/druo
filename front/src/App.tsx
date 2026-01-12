import { useState, useEffect, useCallback } from "react";
import "./App.css";
import * as api from "./api";
import type { Payment, Stats, RetryConfig } from "./types";
import {
  Header,
  StatsGrid,
  SimulatePanel,
  ConfigPanel,
  PaymentsTable,
  Alert,
} from "./components";

function App() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [config, setConfig] = useState<RetryConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [simulating, setSimulating] = useState(false);
  const [message, setMessage] = useState<{
    type: "success" | "error" | "info";
    text: string;
  } | null>(null);

  const merchantId = api.DEMO_MERCHANT_ID;

  // Cargar datos
  const loadData = useCallback(async () => {
    try {
      const [statsData, paymentsData, configData] = await Promise.all([
        api.getStats(merchantId),
        api.getPayments(merchantId),
        api.getRetryConfig(merchantId),
      ]);
      setStats(statsData);
      setPayments(paymentsData.payments || paymentsData);
      setConfig(configData);
    } catch (error) {
      console.error("Error loading data:", error);
      setMessage({ type: "error", text: "Error conectando con el backend" });
    } finally {
      setLoading(false);
    }
  }, [merchantId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Simular fallo
  const handleSimulate = async (failureType: string) => {
    setSimulating(true);
    setMessage(null);
    try {
      const result = await api.simulateFailure(merchantId, failureType);
      setMessage({
        type: "success",
        text: `✓ Pago ${result.payment_id.slice(0, 8)}... creado. ${
          result.message
        }`,
      });
      loadData();
    } catch (error) {
      setMessage({ type: "error", text: "Error simulando fallo" });
    } finally {
      setSimulating(false);
    }
  };

  // Update config
  const handleUpdateConfig = async (updates: Partial<RetryConfig>) => {
    if (!config) return;
    try {
      const newConfig = await api.updateRetryConfig(merchantId, updates);
      setConfig(newConfig);
      setMessage({
        type: "success",
        text: "Configuración actualizada",
      });
    } catch (error) {
      setMessage({ type: "error", text: "Error actualizando configuración" });
      throw error;
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Cargando dashboard...</p>
      </div>
    );
  }

  return (
    <div className="app">
      <Header
        title="🔄 Payment Retry Dashboard"
        subtitle="Sistema automático de reintentos de pagos fallidos"
      />

      {message && (
        <Alert
          type={message.type}
          message={message.text}
          onClose={() => setMessage(null)}
        />
      )}

      <StatsGrid stats={stats} />

      <div className="main-grid">
        <SimulatePanel onSimulate={handleSimulate} disabled={simulating} />
        <ConfigPanel config={config} onUpdateConfig={handleUpdateConfig} />
      </div>

      <PaymentsTable payments={payments} onRefresh={loadData} />

      <footer className="footer">
        <p>
          <a
            href="http://localhost:5678"
            target="_blank"
            rel="noopener noreferrer"
          >
            🔧 n8n Workflow
          </a>
          <span className="separator">|</span>
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
          >
            📚 API Docs
          </a>
        </p>
      </footer>
    </div>
  );
}

export default App;
