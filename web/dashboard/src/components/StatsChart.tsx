import { useEffect, useState } from "react";
import { fetchStats, type Stats } from "../api";
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, BarElement, Tooltip, Legend } from "chart.js";
import { Line } from "react-chartjs-2";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Tooltip, Legend);

export function StatsChart() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setError(null);
      try {
        const s = await fetchStats(24);
        if (!cancelled) setStats(s);
      } catch (e: unknown) {
        const err = e as Error;
        if (!cancelled) setError(err?.message ?? "Error");
      }
    }
    load();
    const id = setInterval(load, 10000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  if (error) return <div style={{ color: "red" }}>{error}</div>;
  if (!stats) return <div>Loading chart…</div>;

  const labels = stats.timeline.map(p => new Date(p.t * 1000).toLocaleTimeString());
  const data = {
    labels,
    datasets: [
      {
        label: "GRANTED",
        data: stats.timeline.map(p => p.granted),
        borderColor: "green",
        backgroundColor: "rgba(0,128,0,0.2)",
      },
      {
        label: "DENIED",
        data: stats.timeline.map(p => p.denied),
        borderColor: "crimson",
        backgroundColor: "rgba(220,20,60,0.2)",
      }
    ]
  };

  const total = stats.total;

  return (
    <div>
      <h2>Activity last 24h (Total: GRANTED {total.GRANTED} / DENIED {total.DENIED})</h2>
      <Line data={data} />
    </div>
  );
}


