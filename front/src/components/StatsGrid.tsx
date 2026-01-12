// Componente StatsGrid
import type { Stats } from "../types";

interface StatsGridProps {
  stats: Stats | null;
}

// Formatea centavos a moneda
function formatCurrency(cents: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(cents / 100);
}

export function StatsGrid({ stats }: StatsGridProps) {
  return (
    <div className="stats-grid">
      <div className="stat-card">
        <h3>Total Pagos</h3>
        <div className="value">{stats?.total_payments || 0}</div>
      </div>
      <div className="stat-card success">
        <h3>Recuperados</h3>
        <div className="value">{stats?.recovered_count || 0}</div>
        <div className="amount">
          {formatCurrency(stats?.recovered_amount_cents || 0)}
        </div>
      </div>
      <div className="stat-card warning">
        <h3>En Reintento</h3>
        <div className="value">{stats?.retrying_count || 0}</div>
        <div className="amount">
          {formatCurrency(stats?.retrying_amount_cents || 0)}
        </div>
      </div>
      <div className="stat-card danger">
        <h3>Perdidos</h3>
        <div className="value">
          {(stats?.failed_count || 0) + (stats?.exhausted_count || 0)}
        </div>
        <div className="amount">
          {formatCurrency(stats?.lost_amount_cents || 0)}
        </div>
      </div>
      <div className="stat-card info">
        <h3>Tasa Recuperación</h3>
        <div className="value">{stats?.recovery_rate || "0%"}</div>
      </div>
    </div>
  );
}
