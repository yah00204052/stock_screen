const SP500_SAMPLE = [
  'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK.B',
  'JNJ', 'V', 'XOM', 'UNH', 'JPM', 'MA', 'PG', 'HD', 'CVX', 'MRK', 'ABBV', 'PEP',
]

export default function FilterPanel({ filters, onChange, onScreen, loading }) {
  const set = (key, value) => onChange({ ...filters, [key]: value })

  return (
    <div className="filter-panel">
      <h2>Filters</h2>

      <div className="form-group">
        <label>Tickers</label>
        <textarea
          value={filters.tickers}
          onChange={e => set('tickers', e.target.value)}
          placeholder={'AAPL, MSFT, GOOGL\nor one per line'}
          rows={5}
        />
        <button className="btn-secondary" onClick={() => set('tickers', SP500_SAMPLE.join(', '))}>
          Load S&P 500 sample ({SP500_SAMPLE.length})
        </button>
      </div>

      <div className="form-group">
        <label>Min Market Cap (billions)</label>
        <input
          type="number"
          value={filters.min_cap}
          onChange={e => set('min_cap', e.target.value)}
          placeholder="e.g. 10"
          min="0"
        />
      </div>

      <div className="form-group">
        <label>Sector (partial match)</label>
        <input
          type="text"
          value={filters.sector}
          onChange={e => set('sector', e.target.value)}
          placeholder="e.g. Technology"
        />
      </div>

      <div className="form-group">
        <label>Technical Filters</label>
        <div className="checkboxes">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={filters.require_ma_bullish}
              onChange={e => set('require_ma_bullish', e.target.checked)}
            />
            MA20 &gt; MA50 (bullish crossover)
          </label>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={filters.require_above_resistance}
              onChange={e => set('require_above_resistance', e.target.checked)}
            />
            Price above 20-day high
          </label>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={filters.require_high_volume}
              onChange={e => set('require_high_volume', e.target.checked)}
            />
            Volume above 20-day average
          </label>
        </div>
      </div>

      <button className="btn-primary" onClick={onScreen} disabled={loading}>
        {loading ? 'Screening…' : 'Screen Stocks'}
      </button>
    </div>
  )
}
