import { announcements, users } from '../data/catalog'

function mapAvis(avis) {
  const utilisateur = users.find((user) => user.id === avis.utilisateur_id)
  const annonce = announcements.find((item) => item.id === avis.annonce_id)

  return {
    id: avis.idAvis,
    utilisateur_id: avis.utilisateur_id,
    annonce_id: avis.annonce_id,
    reservation_id: avis.reservation_id,
    item: annonce?.name ?? `Annonce ${avis.annonce_id}`,
    owner: utilisateur?.name ?? `Utilisateur ${avis.utilisateur_id}`,
    rating: avis.note,
    comment: avis.commentaire,
    date: new Intl.DateTimeFormat('fr-FR', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    }).format(new Date(avis.dateAvis)),
  }
}

export async function getAvis() {
  const response = await fetch('/api/avis/')
  if (!response.ok) throw new Error('Impossible de charger les avis')
  const data = await response.json()
  return data.map(mapAvis)
}

export async function createAvis(payload) {
  const response = await fetch('/api/avis/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw new Error(JSON.stringify(await response.json()))
  return response.json()
}

export async function updateAvis(id, payload) {
  const response = await fetch(`/api/avis/${id}/`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) throw new Error(JSON.stringify(await response.json()))
  return response.json()
}

export async function deleteAvis(id) {
  const response = await fetch(`/api/avis/${id}/`, { method: 'DELETE' })
  if (!response.ok) throw new Error('Impossible de supprimer cet avis')
}
