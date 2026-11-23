/* eslint-disable react-refresh/only-export-components */
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { api, tokens } from '../api/client'

const AuthContext = createContext(null)

/** Utilisateur connecté et actions d'authentification, disponibles partout avec useAuth(). */
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(Boolean(tokens.access || tokens.refresh))

  useEffect(() => {
    if (!tokens.access && !tokens.refresh) return
    api('/users/me/')
      .then(setUser)
      .catch(() => tokens.clear())
      .finally(() => setLoading(false))
  }, [])

  const login = useCallback(async (email, password) => {
    const data = await api('/auth/login/', { method: 'POST', body: { email, password } })
    tokens.save(data)
    setUser(data.user)
    return data.user
  }, [])

  const register = useCallback(async (fields) => {
    const data = await api('/auth/register/', { method: 'POST', body: fields })
    tokens.save(data)
    setUser(data.user)
    return data.user
  }, [])

  // US02 — déconnexion : le navigateur oublie ses jetons
  const logout = useCallback(async () => {
    tokens.clear()
    setUser(null)
  }, [])

  const deleteAccount = useCallback(async () => {
    await api('/users/me/', { method: 'DELETE' })
    tokens.clear()
    // l'utilisateur est retiré au tour suivant, après la redirection faite par la page
    setTimeout(() => setUser(null), 0)
  }, [])

  const value = useMemo(
    () => ({ user, loading, login, register, logout, deleteAccount, setUser }),
    [user, loading, login, register, logout, deleteAccount],
  )
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  return useContext(AuthContext)
}
