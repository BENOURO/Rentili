import { api } from '../api/client'

function mapAvis(avis) {
  return {
    id: avis.idAvis,
    utilisateur_id: avis.utilisateur_id,
    annonce_id: avis.annonce_id,
    reservation_id: avis.reservation_id,
    item: avis.annonce_titre ?? `Annonce ${avis.annonce_id}`,
    owner: avis.proprietaire_name ?? `Propriétaire ${avis.annonce_id}`,
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

export async function getEligibleAvis() {
  return api('/avis/eligible/')
}

export async function createAvis(payload) {
  return api('/avis/', { method: 'POST', body: payload })
}

export async function updateAvis(id, payload) {
  return api(`/avis/${id}/`, { method: 'PATCH', body: payload })
}

export async function deleteAvis(id) {
  return api(`/avis/${id}/`, { method: 'DELETE' })
}
