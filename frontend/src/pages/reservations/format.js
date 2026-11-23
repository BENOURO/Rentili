/** Petits utilitaires d'affichage du module « Gestion des réservations ». */

const jour = new Intl.DateTimeFormat('fr-FR', { day: 'numeric', month: 'short', year: 'numeric' })

/** '2026-11-28' → '28 nov. 2026' (la date est lue en heure locale, pas en UTC). */
export function dateFr(iso) {
  const [y, m, d] = iso.split('-').map(Number)
  return jour.format(new Date(y, m - 1, d))
}

export function periode(debut, fin) {
  return debut === fin ? dateFr(debut) : `du ${dateFr(debut)} au ${dateFr(fin)}`
}

export function dt(montant) {
  const n = Number(montant)
  return `${Number.isInteger(n) ? n : n.toFixed(2)} DT`
}

/** Nombre de jours facturés : le jour de début et le jour de fin comptent tous les deux. */
export function nbJours(debut, fin) {
  if (!debut || !fin) return 0
  const ms = new Date(fin) - new Date(debut)
  return ms < 0 ? 0 : Math.round(ms / 86400000) + 1
}

/** Date du jour au format AAAA-MM-JJ (heure locale), pour l'attribut min des champs date. */
export function aujourdhui() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

export const STATUTS = {
  EN_ATTENTE: { label: 'En attente', cls: 'st-attente' },
  ACCEPTEE: { label: 'Acceptée', cls: 'st-acceptee' },
  REFUSEE: { label: 'Refusée', cls: 'st-refusee' },
  ANNULEE: { label: 'Annulée', cls: 'st-annulee' },
  TERMINEE: { label: 'Terminée', cls: 'st-terminee' },
}
