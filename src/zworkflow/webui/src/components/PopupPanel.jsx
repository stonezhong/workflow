import { useEffect, useRef } from 'react'

const popupStack = []

export default function PopupPanel({ title, ariaLabel, className = '', onClose, children }) {
  const panelRef = useRef(null)
  const stackItemRef = useRef(null)
  const onCloseRef = useRef(onClose)

  onCloseRef.current = onClose

  useEffect(() => {
    const stackItem = {
      panelRef,
      close: () => onCloseRef.current(),
    }

    stackItemRef.current = stackItem
    popupStack.push(stackItem)
    panelRef.current?.focus()

    const handleWindowKeyDown = event => {
      if (event.key !== 'Escape') return
      if (popupStack[popupStack.length - 1] !== stackItem) return

      event.stopImmediatePropagation()
      stackItem.close()
    }

    window.addEventListener('keydown', handleWindowKeyDown)

    return () => {
      window.removeEventListener('keydown', handleWindowKeyDown)

      const index = popupStack.indexOf(stackItem)
      if (index !== -1) popupStack.splice(index, 1)

      const nextPopup = popupStack[popupStack.length - 1]
      window.requestAnimationFrame(() => {
        nextPopup?.panelRef.current?.focus()
      })
    }
  }, [])

  const handleKeyDown = event => {
    if (event.key !== 'Escape') return
    if (popupStack[popupStack.length - 1] !== stackItemRef.current) return

    event.stopPropagation()
    onCloseRef.current()
  }

  return (
    <div className="popup-overlay" role="presentation">
      <section
        ref={panelRef}
        className={`popup-panel ${className}`.trim()}
        role="dialog"
        aria-modal="true"
        aria-label={ariaLabel ?? title}
        tabIndex="-1"
        onKeyDown={handleKeyDown}
      >
        <div className="popup-header">
          <h3>{title}</h3>
          <button
            type="button"
            className="secondary-button popup-close-button"
            onClick={onClose}
          >
            Close
          </button>
        </div>
        {children}
      </section>
    </div>
  )
}
