import { useEffect, useState } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer,
} from 'recharts'

const fmtTick = (v) => (v != null ? `$${Number(v).toFixed(0)}` : '')
const fmtTooltip = (v) => (v != null ? `$${Number(v).toFixed(2)}` : 'N/A')

export default function StockChart({ ticker, onClose }) {
  const [chartData, setChartData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    setChartData(null)
    fetch(`/api/stock/${encodeURIComponent(ticker)}/history`)
      .then(r => {
        if (!r.ok) throw new Error('Failed to load history')
        return r.json()
      })
      .then(data => {
        const points = data.dates.map((d, i) => ({
          date: d,
          Close: data.close[i],
          MA20: data.ma20[i],
          MA50: data.ma50[i],
        }))
        // Last 180 trading days ≈ 6 months
        setChartData(points.slice(-180))
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [ticker])

  const tickInterval = chartData ? Math.floor(chartData.length / 8) : 1

  return (
    <div className="chart-panel">
      <div className="chart-header">
        <h3>{ticker} — Price &amp; Moving Averages (6 months)</h3>
        <button className="btn-close" onClick={onClose} aria-label="Close chart">✕</button>
      </div>

      {loading && <div className="chart-loading">Loading chart…</div>}
      {error && <div className="error-banner">{error}</div>}

      {chartData && !loading && (
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData} margin={{ top: 5, right: 24, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis
              dataKey="date"
              tickFormatter={d => d.slice(5)}
              interval={tickInterval}
              tick={{ fontSize: 11, fill: '#64748b' }}
            />
            <YAxis
              tickFormatter={fmtTick}
              domain={['auto', 'auto']}
              tick={{ fontSize: 11, fill: '#64748b' }}
              width={56}
            />
            <Tooltip formatter={fmtTooltip} />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Line
              type="monotone"
              dataKey="Close"
              stroke="#2563eb"
              dot={false}
              strokeWidth={1.5}
              connectNulls={false}
            />
            <Line
              type="monotone"
              dataKey="MA20"
              stroke="#f59e0b"
              dot={false}
              strokeWidth={1.5}
              strokeDasharray="5 3"
              connectNulls={false}
            />
            <Line
              type="monotone"
              dataKey="MA50"
              stroke="#ef4444"
              dot={false}
              strokeWidth={1.5}
              strokeDasharray="5 3"
              connectNulls={false}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
