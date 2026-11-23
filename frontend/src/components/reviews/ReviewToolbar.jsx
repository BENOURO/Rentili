export default function ReviewToolbar({ search, filter, onSearchChange, onFilterChange }) {
  return (
    <div className="review-toolbar card">
      <input
        className="input search"
        type="search"
        value={search}
        onChange={(event) => onSearchChange(event.target.value)}
        placeholder="Rechercher un objet ou un avis"
      />
      <div className="filter-buttons" aria-label="Filtrer les avis">
        <button className={filter === 'all' ? 'filter active' : 'filter'} type="button" onClick={() => onFilterChange('all')}>Tous</button>
        <button className={filter === 'positive' ? 'filter active' : 'filter'} type="button" onClick={() => onFilterChange('positive')}>Positifs</button>
        <button className={filter === 'low' ? 'filter active' : 'filter'} type="button" onClick={() => onFilterChange('low')}>À améliorer</button>
      </div>
    </div>
  )
}
