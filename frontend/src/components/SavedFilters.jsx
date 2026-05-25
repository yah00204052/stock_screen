import { useState } from 'react'

export default function SavedFilters({ savedFilters, onSave, onLoad, onDelete }) {
  const [name, setName] = useState('')

  const handleSave = () => {
    const trimmed = name.trim()
    if (!trimmed) return
    onSave(trimmed)
    setName('')
  }

  const names = Object.keys(savedFilters)

  return (
    <div className="saved-filters">
      <h2>Saved Filters</h2>

      <div className="save-row">
        <input
          type="text"
          value={name}
          onChange={e => setName(e.target.value)}
          placeholder="Name this filter set…"
          onKeyDown={e => e.key === 'Enter' && handleSave()}
        />
        <button className="btn-secondary" onClick={handleSave} disabled={!name.trim()}>
          Save
        </button>
      </div>

      {names.length === 0 ? (
        <p className="empty-saved">No saved filters yet.</p>
      ) : (
        <ul className="saved-list">
          {names.map(n => (
            <li key={n}>
              <button className="btn-load" onClick={() => onLoad(n)} title={`Load "${n}"`}>
                {n}
              </button>
              <button
                className="btn-delete"
                onClick={() => onDelete(n)}
                aria-label={`Delete "${n}"`}
              >
                ✕
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
