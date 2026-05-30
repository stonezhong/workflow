import { useEffect, useRef } from 'react'

const popupStack = []

export default function PopupPanel({ title, ariaLabel, className = '', onClose, children }) {
  const panelRef = useRef(null)
  const stackItemRef = useRef(null)
  const onCloseRef = useRef(onClose)
  const dragCleanupRef = useRef(null)

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
      dragCleanupRef.current?.()

      const index = popupStack.indexOf(stackItem)
      if (index !== -1) popupStack.splice(index, 1)

      const nextPopup = popupStack[popupStack.length - 1]
      window.requestAnimationFrame(() => {
        nextPopup?.panelRef.current?.focus()
      })
    }
  }, [])

  const handlePointerDown = event => {
    if (event.button !== 0 || event.target.closest('button')) return

    const panel = panelRef.current
    if (!panel) return

    const rect = panel.getBoundingClientRect()
    const offsetX = event.clientX - rect.left
    const offsetY = event.clientY - rect.top

    panel.style.left = `${rect.left}px`
    panel.style.top = `${rect.top}px`
    panel.style.transform = 'none'

    const handlePointerMove = moveEvent => {
      const maxLeft = Math.max(0, window.innerWidth - panel.offsetWidth)
      const maxTop = Math.max(0, window.innerHeight - panel.offsetHeight)

      panel.style.left = `${Math.min(Math.max(0, moveEvent.clientX - offsetX), maxLeft)}px`
      panel.style.top = `${Math.min(Math.max(0, moveEvent.clientY - offsetY), maxTop)}px`
    }

    const stopDragging = () => {
      window.removeEventListener('pointermove', handlePointerMove)
      window.removeEventListener('pointerup', stopDragging)
      dragCleanupRef.current = null
    }

    dragCleanupRef.current?.()
    dragCleanupRef.current = stopDragging
    window.addEventListener('pointermove', handlePointerMove)
    window.addEventListener('pointerup', stopDragging)
    event.preventDefault()
  }

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
        <div className="popup-header" onPointerDown={handlePointerDown}>
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
