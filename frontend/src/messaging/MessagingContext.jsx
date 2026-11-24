/* eslint-disable react-refresh/only-export-components */
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'
import { api, tokens } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import './messaging.css'

const MessagingContext = createContext({ unread: 0, connected: false, subscribe: () => () => {}, refreshUnread: () => {} })

function socketUrl() {
  const base = import.meta.env.VITE_WS_URL || `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/ws/messaging/`
  return `${base}?token=${encodeURIComponent(tokens.access || '')}`
}

/** Connexion WebSocket unique (temps réel), nombre de messages non lus, et abonnement aux événements avec subscribe(fn). */
export function MessagingProvider({ children }) {
  const { user } = useAuth()
  const userId = user?.id
  const [unread, setUnread] = useState(0)
  const [connected, setConnected] = useState(false)
  const listeners = useRef(new Set())

  const refreshUnread = useCallback(() => api('/messaging/unread-count/').then((d) => setUnread(d.count)).catch(() => {}), [])
  const subscribe = useCallback((fn) => { listeners.current.add(fn); return () => listeners.current.delete(fn) }, [])

  useEffect(() => {
    if (!userId) return
    let socket, retry, ping, attempts = 0, stopped = false
    refreshUnread()

    function open() {
      if (stopped) return
      socket = new WebSocket(socketUrl())
      socket.onopen = () => {
        attempts = 0
        setConnected(true)
        refreshUnread() // rattrape ce qui a pu arriver pendant une coupure
        ping = setInterval(() => socket.readyState === 1 && socket.send(JSON.stringify({ type: 'ping' })), 30000)
      }
      socket.onmessage = (e) => {
        const evt = JSON.parse(e.data)
        if (evt.event === 'pong') return
        listeners.current.forEach((fn) => fn(evt))
        refreshUnread()
      }
      socket.onclose = async (e) => {
        clearInterval(ping)
        setConnected(false)
        if (stopped) return
        if (e.code === 4401) await api('/users/me/').catch(() => {}) // jeton expiré : renouvelé par le client HTTP
        retry = setTimeout(open, Math.min(1000 * 2 ** attempts++, 15000))
      }
    }
    open()
    return () => { stopped = true; clearTimeout(retry); clearInterval(ping); socket?.close() }
  }, [userId, refreshUnread])

  const shownUnread = userId ? unread : 0 // déconnecté : pas de compteur
  const value = useMemo(() => ({ unread: shownUnread, connected, subscribe, refreshUnread }), [shownUnread, connected, subscribe, refreshUnread])
  return <MessagingContext.Provider value={value}>{children}</MessagingContext.Provider>
}

export function useMessaging() {
  return useContext(MessagingContext)
}