import './App.css'
import { TransactionsTable } from './components/TransactionsTable'
import { StatsChart } from './components/StatsChart'

function App() {
  return (
    <>
      <div style={{ maxWidth: 1200, margin: "0 auto", padding: 16 }}>
        <h1>NFC Dashboard</h1>
        <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: 24 }}>
          <StatsChart />
          <TransactionsTable />
        </div>
      </div>
    </>
  )
}

export default App
