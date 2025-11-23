export const API_BASE = import.meta.env.VITE_API_BASE || "/api";

export type Transaction = {
  _id: string;
  uid: string;
  status: "GRANTED" | "DENIED";
  timestamp: number;
};

export type Stats = {
  since: number;
  now: number;
  total: { GRANTED: number; DENIED: number };
  timeline: { t: number; granted: number; denied: number }[];
};

export async function fetchTransactions(limit = 100): Promise<Transaction[]> {
  const res = await fetch(`${API_BASE}/transactions?limit=${limit}`, {
    credentials: "include",
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch transactions: ${res.status}`);
  }
  return res.json();
}

export async function fetchStats(hours = 24): Promise<Stats> {
  const res = await fetch(`${API_BASE}/stats?hours=${hours}`, {
    credentials: "include",
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch stats: ${res.status}`);
  }
  return res.json();
}


