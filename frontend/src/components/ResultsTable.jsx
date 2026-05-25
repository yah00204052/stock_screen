import { useState } from 'react'

const fmtCap = (v) => {
  if (!v) return '—'
  if (v >= 1e12) return `$${(v / 1e12).toFixed(1)}T`
  if (v >= 1e9) return `$${(v / 1e9).toFixed(1)}B`
  if (v >= 1e6) return `$${(v / 1e6).toFixed(1)}M`
  return `$${v.toLocaleString()}`
}
const fmtPrice = (v) => (v != null ? `$${v.toFixed(2)}` : '—')
const fmtVol = (v) => (v != null ? `${(v / 1e6).toFixed(1)}M` : '—')

const Bool = ({ value }) => (
  <span className={`indicator ${value ? 'yes' : 'no'}`}>{value ? '✓' : '✗'}</span>
)

const COLUMNS = [
  { key: 'ticker', label: 'Ticker' },
  { key: 'name', label: 'Name', wide: true },
  { key: 'sector', label: 'Sector', wide: true },
  { key: 'price', label: 'Price', fmt: fmtPrice, numeric: true },
  { key: 'market_cap', label: 'Market Cap', fmt: fmtCap, numeric: true },
  { key: 'ma_20', label: 'MA 20', fmt: fmtPrice, numeric: true },
  { key: 'ma_50', label: 'MA 50', fmt: fmtPrice, numeric: true },
  { key: 'resistance', label: 'Resistance', fmt: fmtPrice, numeric: true },
  { key: 'current_volume', label: 'Volume', fmt: fmtVol, numeric: true },
  { key: 'avg_volume', label: 'Avg Vol', fmt: fmtVol, numeric: true },
  { key: 'ma_bullish', label: 'MA Bull', bool: true },
  { key: 'above_resistance', label: 'Above Res', bool: true },
  { key: 'high_volume', label: 'High Vol', bool: true },
]

export default function ResultsTable({ results, onSelectTicker, selectedTicker }) {
  const [sortKey, setSortKey] = useState('ticker')
  const [sortDir, setSortDir] = useState('asc')

  const handleSort = (key) => {
    if (sortKey === key) {
      setSortDir(d => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortKey(key)
      setSortDir('asc')
    }
  }

  const sorted = [...results].sort((a, b) => {
    const va = a[sortKey]
    const vb = b[sortKey]
    if (va == null) return 1
    if (vb == null) return -1
    const cmp = va < vb ? -1 : va > vb ? 1 : 0
    return sortDir === 'asc' ? cmp : -cmp
  })

  if (results.length === 0) {
    return (
      <div className="no-results">No stocks matched the current criteria.</div>
    )
  }

  return (
    <div className="table-wrapper">
      <table className="results-table">
        <thead>
          <tr>
            {COLUMNS.map(col => (
              <th
                key={col.key}
                onClick={() => handleSort(col.key)}
                className={[
                  col.numeric ? 'col-num' : '',
                  sortKey === col.key ? 'sorted' : '',
                ].join(' ')}
              >
                {col.label}
                {sortKey === col.key && (
                  <span className="sort-arrow">{sortDir === 'asc' ? ' ↑' : ' ↓'}</span>
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map(row => (
            <tr
              key={row.ticker}
              onClick={() => onSelectTicker(row.ticker)}
              className={row.ticker === selectedTicker ? 'selected' : ''}
            >
              {COLUMNS.map(col => (
                <td key={col.key} className={col.numeric ? 'col-num' : ''}>
                  {col.bool ? (
                    <Bool value={row[col.key]} />
                  ) : col.fmt ? (
                    col.fmt(row[col.key])
                  ) : (
                    row[col.key] || '—'
                  )}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
