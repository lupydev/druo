// API client - usando fetch nativo

// Lee la URL base desde la variable de entorno Vite `VITE_API_URL`.
// Para evitar exponer un valor por defecto en el bundle, requerimos
// que la variable exista. Copia `front/.env.example` → `front/.env`.
const API_URL = import.meta.env.VITE_API_URL;
if (!API_URL) {
  throw new Error(
    "VITE_API_URL no está definida. Copia front/.env.example a front/.env y configura VITE_API_URL"
  );
}

// Merchant ID de demo (del seed de la DB)
export const DEMO_MERCHANT_ID = "466fd34b-96a1-4635-9b2c-dedd2645291f";

export async function getStats(merchantId: string) {
  const res = await fetch(`${API_URL}/simulate/stats/${merchantId}`);
  if (!res.ok) throw new Error("Error fetching stats");
  return res.json();
}

export async function getPayments(merchantId: string) {
  const res = await fetch(
    `${API_URL}/payments/?merchant_id=${merchantId}&limit=20`
  );
  if (!res.ok) throw new Error("Error fetching payments");
  return res.json();
}

export async function getRetryConfig(merchantId: string) {
  const res = await fetch(`${API_URL}/retry-config/${merchantId}`);
  if (!res.ok) throw new Error("Error fetching config");
  return res.json();
}

export async function updateRetryConfig(
  merchantId: string,
  config: Record<string, unknown>
) {
  const res = await fetch(`${API_URL}/retry-config/${merchantId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config),
  });
  if (!res.ok) throw new Error("Error updating config");
  return res.json();
}

export async function simulateFailure(merchantId: string, failureType: string) {
  const amountCents = Math.floor(Math.random() * (100000 - 1000 + 1)) + 1000;
  const processors = ["stripe", "pse", "nequi", "dlocale"];
  const processor = processors[Math.floor(Math.random() * processors.length)];

  const res = await fetch(`${API_URL}/simulate/failure`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      merchant_id: merchantId,
      amount_cents: amountCents,
      failure_type: failureType,
      processor: processor,
    }),
  });
  if (!res.ok) throw new Error("Error simulating failure");
  return res.json();
}
