// Componente ConfigPanel
import { useState } from "react";
import type { RetryConfig } from "../types";

interface ConfigPanelProps {
  config: RetryConfig | null;
  onUpdateConfig: (updates: Partial<RetryConfig>) => Promise<void>;
}

interface FailureTypeConfig {
  key: string;
  label: string;
  enabledField: keyof RetryConfig;
  delayField: keyof RetryConfig;
  successRate: string;
}

const FAILURE_TYPES: FailureTypeConfig[] = [
  {
    key: "network_timeout",
    label: "Network Timeout",
    enabledField: "network_timeout_enabled",
    delayField: "network_timeout_delay",
    successRate: "60%",
  },
  {
    key: "insufficient_funds",
    label: "Fondos Insuficientes",
    enabledField: "insufficient_funds_enabled",
    delayField: "insufficient_funds_delay",
    successRate: "20%",
  },
  {
    key: "card_declined",
    label: "Tarjeta Rechazada",
    enabledField: "card_declined_enabled",
    delayField: "card_declined_delay",
    successRate: "15%",
  },
];

export function ConfigPanel({ config, onUpdateConfig }: ConfigPanelProps) {
  const [updating, setUpdating] = useState<string | null>(null);
  const [editingDelay, setEditingDelay] = useState<string | null>(null);
  const [tempDelay, setTempDelay] = useState<number>(0);

  const handleToggleMain = async () => {
    if (!config) return;
    setUpdating("main");
    try {
      await onUpdateConfig({ retry_enabled: !config.retry_enabled });
    } finally {
      setUpdating(null);
    }
  };

  const handleToggleType = async (enabledField: keyof RetryConfig) => {
    if (!config) return;
    setUpdating(enabledField as string);
    try {
      await onUpdateConfig({ [enabledField]: !config[enabledField] });
    } finally {
      setUpdating(null);
    }
  };

  const handleMaxAttemptsChange = async (delta: number) => {
    if (!config) return;
    const newValue = Math.max(1, Math.min(10, config.max_attempts + delta));
    if (newValue === config.max_attempts) return;
    setUpdating("max_attempts");
    try {
      await onUpdateConfig({ max_attempts: newValue });
    } finally {
      setUpdating(null);
    }
  };

  const startEditDelay = (delayField: string, currentValue: number) => {
    setEditingDelay(delayField);
    setTempDelay(currentValue);
  };

  const saveDelay = async (delayField: keyof RetryConfig) => {
    setUpdating(delayField as string);
    try {
      await onUpdateConfig({ [delayField]: tempDelay });
    } finally {
      setUpdating(null);
      setEditingDelay(null);
    }
  };

  const cancelEditDelay = () => {
    setEditingDelay(null);
  };

  return (
    <div className="section">
      <div className="section-header">
        <h2>⚙️ Configuración de Reintentos</h2>
      </div>
      <div className="section-body">
        {/* Toggle principal */}
        <div className="config-row highlight">
          <div className="config-label">
            <span className="config-title">Reintentos Automáticos</span>
            <span className="config-subtitle">
              Habilitar/deshabilitar sistema de reintentos
            </span>
          </div>
          <button
            className={`toggle-btn ${config?.retry_enabled ? "active" : ""}`}
            onClick={handleToggleMain}
            disabled={updating === "main"}
          >
            {updating === "main" ? "..." : config?.retry_enabled ? "ON" : "OFF"}
          </button>
        </div>

        {/* Máximo de intentos */}
        <div className="config-row">
          <div className="config-label">
            <span className="config-title">Máximo de intentos</span>
            <span className="config-subtitle">
              Número de reintentos antes de desistir
            </span>
          </div>
          <div className="number-input">
            <button
              className="number-btn"
              onClick={() => handleMaxAttemptsChange(-1)}
              disabled={
                updating === "max_attempts" || (config?.max_attempts || 0) <= 1
              }
            >
              −
            </button>
            <span className="number-value">
              {updating === "max_attempts" ? "..." : config?.max_attempts || 3}
            </span>
            <button
              className="number-btn"
              onClick={() => handleMaxAttemptsChange(1)}
              disabled={
                updating === "max_attempts" || (config?.max_attempts || 0) >= 10
              }
            >
              +
            </button>
          </div>
        </div>

        <div className="config-divider">
          <span>Tipos de Fallo</span>
        </div>

        {/* Configuración por tipo de fallo */}
        {FAILURE_TYPES.map((type) => {
          const isEnabled = config?.[type.enabledField] as boolean;
          const delay = config?.[type.delayField] as number;
          const isEditing = editingDelay === type.delayField;

          return (
            <div key={type.key} className="config-row-expandable">
              <div className="config-row">
                <div className="config-label">
                  <span className="config-title">{type.label}</span>
                  <span className="config-subtitle">
                    Tasa de éxito: {type.successRate}
                  </span>
                </div>
                <button
                  className={`toggle-btn small ${isEnabled ? "active" : ""}`}
                  onClick={() => handleToggleType(type.enabledField)}
                  disabled={updating === type.enabledField}
                >
                  {updating === type.enabledField
                    ? "..."
                    : isEnabled
                    ? "ON"
                    : "OFF"}
                </button>
              </div>

              {isEnabled && (
                <div className="config-sub-row">
                  <span className="config-sub-label">
                    Delay antes de reintentar:
                  </span>
                  {isEditing ? (
                    <div className="delay-edit">
                      <input
                        type="number"
                        className="delay-input"
                        value={tempDelay}
                        onChange={(e) => setTempDelay(Number(e.target.value))}
                        min={1}
                        max={10080}
                      />
                      <span className="delay-unit">min</span>
                      <button
                        className="btn-small btn-success"
                        onClick={() => saveDelay(type.delayField)}
                        disabled={updating === type.delayField}
                      >
                        ✓
                      </button>
                      <button
                        className="btn-small btn-secondary"
                        onClick={cancelEditDelay}
                      >
                        ✗
                      </button>
                    </div>
                  ) : (
                    <button
                      className="delay-display"
                      onClick={() =>
                        startEditDelay(type.delayField as string, delay || 60)
                      }
                    >
                      {delay || 60} min
                      <span className="edit-icon">✎</span>
                    </button>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
