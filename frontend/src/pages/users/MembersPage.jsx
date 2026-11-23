import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api } from '../../api/client'
import MemberCard from './MemberCard'

/** Liste des membres : accès aux profils publics (US05). */
export default function MembersPage() {
  const [params, setParams] = useSearchParams()
  const page = Number(params.get('page') || 1)
  const [data, setData] = useState(null)

  useEffect(() => {
    api(`/users/?page=${page}`).then(setData).catch(() => setData({ count: 0, results: [] }))
  }, [page])

  const pages = data ? Math.max(1, Math.ceil(data.count / 12)) : 1
  const go = (p) => setParams({ page: String(p) })

  return (
    <div className="wrap page">
      <div className="page-head">
        <div><h1>Membres</h1><p className="muted" style={{ margin: 0 }}>Consultez le profil public d'un membre avant de louer ou de prêter un objet.</p></div>
      </div>
      {data === null ? <p className="muted">Chargement…</p>
        : data.results.length === 0 ? <div className="empty"><h3>Aucun membre pour le moment</h3></div>
        : (
          <>
            <p className="muted small"><b>{data.count}</b> membre{data.count > 1 ? 's' : ''}</p>
            <div className="member-grid">{data.results.map((m) => <MemberCard key={m.id} member={m} />)}</div>
            {pages > 1 && (
              <div className="pager">
                {page > 1 && <button className="btn ghost sm" onClick={() => go(page - 1)}>← Précédent</button>}
                <span className="muted small">Page {page} / {pages}</span>
                {page < pages && <button className="btn ghost sm" onClick={() => go(page + 1)}>Suivant →</button>}
              </div>
            )}
          </>
        )}
    </div>
  )
}
