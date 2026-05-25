import { useState, useCallback } from 'react'
import FilterPanel from './components/FilterPanel'
import ResultsTable from './components/ResultsTable'
import StockChart from './components/StockChart'
import SavedFilters from './components/SavedFilters'

const DEFAULT_FILTERS = {
  tickers: '',
  min_cap: '',
  sector: '',
  require_ma_bullish: false,
  require_above_resistance: false,
  require_high_volume: false,
}

export default function App() {
  const [filters, setFilters] = useState(DEFAULT_FILTERS)
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [selectedTicker, setSelectedTicker] = useState(null)
  const [savedFilters, setSavedFilters] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('savedFilters') || '{}')
    } catch {
      return {}
    }
  })

  const handleScreen = useCallback(async () => {
    const tickerList = filters.tickers
      .split(/[,\n\s]+/)
      .map(t => t.trim().toUpperCase())
      .filter(Boolean)

    if (tickerList.length === 0) {
      setError('Please enter at least one ticker.')
      return
    }

    setLoading(true)
    setError(null)
    setResults(null)
    setSelectedTicker(null)

    try {
      const res = await fetch('/api/screen', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tickers: tickerList,
          min_cap: filters.min_cap ? parseFloat(filters.min_cap) : null,
          sector: filters.sector || null,
          require_ma_bullish: filters.require_ma_bullish,
          require_above_resistance: filters.require_above_resistance,
          require_high_volume: filters.require_high_volume,
        }),
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail || `Server error ${res.status}`)
      }
      setResults(await res.json())
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [filters])

  const handleSaveFilter = (name) => {
    const updated = { ...savedFilters, [name]: { ...filters } }
    setSavedFilters(updated)
    localStorage.setItem('savedFilters', JSON.stringify(updated))
  }

  const handleLoadFilter = (name) => {
    setFilters(savedFilters[name])
  }

  const handleDeleteFilter = (name) => {
    const updated = { ...savedFilters }
    delete updated[name]
    setSavedFilters(updated)
    localStorage.setItem('savedFilters', JSON.stringify(updated))
  }

  const tickerCount = filters.tickers.split(/[,\n\s]+/).filter(t => t.trim()).length

  return (
    <div className="app">
      <header className="app-header">
        <h1>Stock Screener</h1>
        <span className="app-subtitle">Technical &amp; Fundamental Analysis</span>
      </header>
      <div className="app-body">
        <aside className="sidebar">
          <FilterPanel
            filters={filters}
            onChange={setFilters}
            onScreen={handleScreen}
            loading={loading}
          />
          <SavedFilters
            savedFilters={savedFilters}
            onSave={handleSaveFilter}
            onLoad={handleLoadFilter}
            onDelete={handleDeleteFilter}
          />
        </aside>
        <main className="main-content">
          {error && <div className="error-banner">{error}</div>}

          {loading && (
            <div className="loading">
              <div className="spinner" />
              <p>Fetching data for {tickerCount} ticker{tickerCount !== 1 ? 's' : ''}…</p>
              <p className="loading-note">yfinance calls may take 10–30 seconds</p>
            </div>
          )}

          {results !== null && !loading && (
            <>
              <div className="results-header">
                <h2>
                  {results.length} stock{results.length !== 1 ? 's' : ''} matched
                </h2>
                {selectedTicker && (
                  <span className="selected-hint">Click a row again to deselect</span>
                )}
              </div>
              <ResultsTable
                results={results}
                onSelectTicker={t => setSelectedTicker(t === selectedTicker ? null : t)}
                selectedTicker={selectedTicker}
              />
            </>
          )}

          {selectedTicker && (
            <StockChart ticker={selectedTicker} onClose={() => setSelectedTicker(null)} />
          )}

          {results === null && !loading && !error && (
            <div className="empty-state">
              <div className="empty-icon">📈</div>
              <p>Enter tickers and set your filters, then click <strong>Screen Stocks</strong>.</p>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
