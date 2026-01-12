// Componente PaymentsTable
import type { Payment } from "../types";

interface PaymentsTableProps {
  payments: Payment[];
  onRefresh: () => void;
}

function formatCurrency(cents: number): string {
  return `$${(cents / 100).toFixed(2)}`;
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleString("es-CO", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function getStatusClass(status: string): string {
  const statusMap: Record<string, string> = {
    succeeded: "badge-succeeded",
    failed: "badge-failed",
    retrying: "badge-retrying",
    recovered: "badge-recovered",
    exhausted: "badge-exhausted",
  };
  return statusMap[status] || "badge-default";
}

export function PaymentsTable({ payments, onRefresh }: PaymentsTableProps) {
  return (
    <div className="section">
      <div className="section-header">
        <h2>📋 Pagos Recientes</h2>
        <button className="btn btn-primary" onClick={onRefresh}>
          🔄 Refrescar
        </button>
      </div>
      <div className="section-body">
        {payments.length === 0 ? (
          <div className="empty">
            <p>No hay pagos aún.</p>
            <p className="empty-hint">Simula un fallo para comenzar.</p>
          </div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Procesador</th>
                <th>Monto</th>
                <th>Estado</th>
                <th>Tipo de Fallo</th>
                <th>Reintentos</th>
                <th>Fecha</th>
              </tr>
            </thead>
            <tbody>
              {payments.map((payment) => (
                <tr key={payment.id}>
                  <td className="cell-id">{payment.id.slice(0, 8)}...</td>
                  <td className="cell-processor">{payment.processor}</td>
                  <td className="cell-amount">
                    {formatCurrency(payment.amount_cents)}
                  </td>
                  <td>
                    <span className={`badge ${getStatusClass(payment.status)}`}>
                      {payment.status}
                    </span>
                  </td>
                  <td>{payment.failure_type || "—"}</td>
                  <td className="cell-center">{payment.retry_count}</td>
                  <td className="cell-date">
                    {formatDate(payment.created_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
