import { STATUTS } from './format'

export default function StatutBadge({ statut }) {
  const s = STATUTS[statut] || { label: statut, cls: '' }
  return <span className={`statut ${s.cls}`}>{s.label}</span>
}
