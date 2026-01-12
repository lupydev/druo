// Tipos para el dashboard

export interface Payment {
  id: string;
  merchant_id: string;
  amount_cents: number;
  currency: string;
  status: string;
  failure_type: string | null;
  retry_count: number;
  processor: string;
  created_at: string;
}

export interface RetryConfig {
  merchant_id: string;
  retry_enabled: boolean;
  max_attempts: number;
  insufficient_funds_enabled: boolean;
  insufficient_funds_delay: number;
  card_declined_enabled: boolean;
  card_declined_delay: number;
  network_timeout_enabled: boolean;
  network_timeout_delay: number;
}

export interface Stats {
  merchant_id: string;
  total_payments: number;
  status_breakdown: Record<string, number>;
  recovery_rate: string;
  recovered_count: number;
  recovered_amount_cents: number;
  retrying_count: number;
  retrying_amount_cents: number;
  failed_count: number;
  exhausted_count: number;
  lost_amount_cents: number;
}

export interface SimulateResponse {
  payment_id: string;
  status: string;
  failure_type: string;
  retry_scheduled: boolean;
  n8n_triggered: boolean;
  message: string;
}
