/* eslint-disable react-refresh/only-export-components */
import { createContext, useCallback, useContext, useState } from 'react'

const ToastContext = createContext(() => {})

export function ToastProvider({ children }) {
  const [items, setItems] = useState([])
  const notify = useCallback((message, type = 'success') => {
    const id = Date.now() + Math.random()
    setItems((list) => [...list, { id, message, type }])
    setTimeout(() => setItems((list) => list.filter((t) => t.id !== id)), 4500)
  }, [])
  return (
    <ToastContext.Provider value={notify}>
      {children}
      <div className="flashes" aria-live="polite">
        {items.map((t) => <div key={t.id} className={`flash ${t.type}`}>{t.message}</div>)}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast() {
  return useContext(ToastContext)
}
