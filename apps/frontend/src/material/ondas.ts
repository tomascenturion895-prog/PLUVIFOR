/**
 * Agrega la onda (md-ripple) y el anillo de foco (md-focus-ring) oficiales de Material 3 a los
 * controles nativos. Se hace por fuera de React para no tener que reescribir cada botón: los
 * elementos agregados son decorativos y no cambian el nombre accesible ni el comportamiento.
 */
const SELECTOR = ['button:not(.v3d-enlace)', '.encabezado nav a', '.accesos li', 'summary'].join(
  ',',
)

function decorar(el: Element) {
  try {
    if (el.querySelector(':scope > md-ripple')) return
    el.classList.add('con-onda')
    const onda = document.createElement('md-ripple')
    onda.setAttribute('aria-hidden', 'true')
    const foco = document.createElement('md-focus-ring')
    foco.setAttribute('aria-hidden', 'true')
    el.append(onda, foco)
  } catch {
    // Si el nodo se desmontó o muta, no interrumpir la navegación
  }
}

export function instalarOndas(raiz: HTMLElement): () => void {
  const recorrer = (nodo: ParentNode) => nodo.querySelectorAll(SELECTOR).forEach(decorar)
  recorrer(raiz)
  const observador = new MutationObserver((cambios) => {
    for (const c of cambios) {
      c.addedNodes.forEach((n) => {
        if (!(n instanceof Element) || n.localName.startsWith('md-')) return
        if (n.matches(SELECTOR)) decorar(n)
        recorrer(n)
      })
    }
  })
  observador.observe(raiz, { childList: true, subtree: true })
  return () => observador.disconnect()
}
