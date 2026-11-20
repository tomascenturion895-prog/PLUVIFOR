import type { DetailedHTMLProps, HTMLAttributes } from 'react'

type Elemento = DetailedHTMLProps<HTMLAttributes<HTMLElement>, HTMLElement>

declare module 'react' {
  // eslint-disable-next-line @typescript-eslint/no-namespace
  namespace JSX {
    interface IntrinsicElements {
      'md-ripple': Elemento
      'md-focus-ring': Elemento & { inward?: boolean }
      'md-linear-progress': Elemento & { indeterminate?: boolean }
      'md-icon': Elemento
    }
  }
}
