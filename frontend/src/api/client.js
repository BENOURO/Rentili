/**
 * Client HTTP commun à tous les modules.
 *   import { api } from '../api/client'
 *   const annonces = await api('/listings/')
 *   await api('/listings/', { method: 'POST', body: { titre: '…' } })
 * Le jeton JWT est ajouté automatiquement ; s'il a expiré, il est renouvelé une fois puis la requête est rejouée.
 */

const ACCESS = 'rentili.access'
const REFRESH = 'rentili.refresh'

function read(key) {
  try { return localStorage.getItem(key) } catch { return null }
}
function write(key, value) {
  try { value ? localStorage.setItem(key, value) : localStorage.removeItem(key) } catch { /* stockage indisponible */ }
}

export const tokens = {
  get access() { return read(ACCESS) },
  get refresh() { return read(REFRESH) },
  save({ access, refresh }) { write(ACCESS, access); if (refresh) write(REFRESH, refresh) },
  clear() { write(ACCESS, null); write(REFRESH, null) },
}

export class ApiError extends Error {
  constructor(status, data) {
    super((data && data.detail) || `Erreur ${status}`)
    this.status = status
    this.data = data || {}
  }
  /** Messages par champ ({ email: ['…'] }) pour les formulaires. */
  get fields() { return typeof this.data === 'object' ? this.data : {} }
}

let refreshing = null
async function refreshAccess() {
  if (!tokens.refresh) return false
  refreshing ??= fetch('/api/auth/refresh/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh: tokens.refresh }),
  })
    .then(async (res) => {
      if (!res.ok) { tokens.clear(); return false }
      tokens.save(await res.json())
      return true
    })
    .catch(() => false)
    .finally(() => { refreshing = null })
  return refreshing
}

export async function api(path, { method = 'GET', body, retry = true } = {}) {
  const isForm = body instanceof FormData
  const headers = {}
  if (body && !isForm) headers['Content-Type'] = 'application/json'
  if (tokens.access) headers.Authorization = `Bearer ${tokens.access}`

  const res = await fetch(`/api${path}`, { method, headers, body: isForm ? body : body ? JSON.stringify(body) : undefined })

  if (res.status === 401 && retry && !path.startsWith('/auth/') && (await refreshAccess())) {
    return api(path, { method, body, retry: false })
  }
  const text = await res.text()
  const data = text ? JSON.parse(text) : null
  if (!res.ok) throw new ApiError(res.status, data)
  return data
}
