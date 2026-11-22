export const monthYear = (iso) => new Date(iso).toLocaleDateString('fr-FR', { month: 'long', year: 'numeric' })
