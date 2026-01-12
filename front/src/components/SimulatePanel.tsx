// Componente SimulatePanel
interface SimulatePanelProps {
  onSimulate: (failureType: string) => void;
  disabled: boolean;
}

const FAILURE_TYPES = [
  {
    type: "network_timeout",
    label: "Network Timeout",
    successRate: "60%",
    btnClass: "btn-warning",
  },
  {
    type: "insufficient_funds",
    label: "Fondos Insuficientes",
    successRate: "20%",
    btnClass: "btn-primary",
  },
  {
    type: "card_declined",
    label: "Tarjeta Rechazada",
    successRate: "15%",
    btnClass: "btn-danger",
  },
  {
    type: "fraud",
    label: "Fraude",
    successRate: "No retriable",
    btnClass: "btn-secondary",
  },
];

export function SimulatePanel({ onSimulate, disabled }: SimulatePanelProps) {
  return (
    <div className="section">
      <div className="section-header">
        <h2>⚡ Simular Fallo de Pago</h2>
      </div>
      <div className="section-body">
        <p className="section-description">
          Selecciona un tipo de fallo para simular:
        </p>
        <div className="btn-group">
          {FAILURE_TYPES.map((failure) => (
            <button
              key={failure.type}
              className={`btn ${failure.btnClass}`}
              onClick={() => onSimulate(failure.type)}
              disabled={disabled}
            >
              {failure.label} ({failure.successRate})
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
