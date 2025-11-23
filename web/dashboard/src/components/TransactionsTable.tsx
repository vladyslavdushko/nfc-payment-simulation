import { useEffect, useState } from "react";
import { fetchTransactions, type Transaction } from "../api";

export function TransactionsTable() {
  const [rows, setRows] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchTransactions(100);
        if (!cancelled) setRows(data);
      } catch (e: unknown) {
        const err = e as Error;
        if (!cancelled) setError(err?.message ?? "Error");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    const id = setInterval(load, 5000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  return (
    <div style={{ overflowX: "auto" }}>
      <h2>Recent Transactions</h2>
      {loading && <div>Loading…</div>}
      {error && <div style={{ color: "red" }}>{error}</div>}
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th style={{ textAlign: "left", borderBottom: "1px solid #ddd" }}>Time</th>
            <th style={{ textAlign: "left", borderBottom: "1px solid #ddd" }}>UID</th>
            <th style={{ textAlign: "left", borderBottom: "1px solid #ddd" }}>Status</th>
            <th style={{ textAlign: "left", borderBottom: "1px solid #ddd" }}>ID</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => {
            const dt = new Date(r.timestamp * 1000).toLocaleString();
            const color = r.status === "GRANTED" ? "green" : "crimson";
            return (
              <tr key={r._id}>
                <td style={{ padding: "6px 8px", borderBottom: "1px solid #f0f0f0" }}>{dt}</td>
                <td style={{ padding: "6px 8px", borderBottom: "1px solid #f0f0f0" }}>{r.uid}</td>
                <td style={{ padding: "6px 8px", borderBottom: "1px solid #f0f0f0", color }}>{r.status}</td>
                <td style={{ padding: "6px 8px", borderBottom: "1px solid #f0f0f0", fontFamily: "monospace" }}>{r._id}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}


