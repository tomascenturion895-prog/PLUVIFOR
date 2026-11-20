import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import {
  InsigniaAdvertencia,
  InsigniaCategoria,
  InsigniaEstado,
  InsigniaSimulado,
} from './Insignias'
import { ADVERTENCIAS, textoMm, type CodigoAdvertencia } from './insignias-datos'

describe('insignias de estado', () => {
  it('dato', () => {
    render(<InsigniaEstado estado="dato" />)
    expect(screen.getByText('Dato')).toBeInTheDocument()
  })

  it('sin fila se muestra como «Sin dato»', () => {
    render(<InsigniaEstado estado="sin_fila" />)
    expect(screen.getByText('Sin dato')).toBeInTheDocument()
  })

  it('fila sin valor se distingue de sin fila', () => {
    render(<InsigniaEstado estado="fila_sin_valor" />)
    expect(screen.getByText('Fila sin valor')).toBeInTheDocument()
  })

  it.each(['sin_fila', 'fila_sin_valor'] as const)(
    'un hueco (%s) nunca usa el texto ni la clase de un cero ni de un dato',
    (estado) => {
      const { container } = render(<InsigniaEstado estado={estado} />)
      const insignia = container.querySelector('.insignia')!
      expect(insignia.textContent).not.toMatch(/\b0\b/)
      expect(insignia).not.toHaveClass('insignia-dato')
      expect(insignia.textContent).toMatch(/no significa que no haya llovido/i)
    },
  )

  it('no depende solo del color: lleva símbolo propio y descripción accesible', () => {
    const { container } = render(<InsigniaEstado estado="sin_fila" />)
    expect(container.querySelector('.insignia-simbolo')).toHaveAttribute('aria-hidden', 'true')
    expect(container.querySelector('.insignia')).toHaveAttribute('title')
    expect(container.querySelector('.sr-only')).toBeInTheDocument()
  })
})

describe('insignias de categoría', () => {
  it.each([
    ['observado', 'Observado'],
    ['referencia', 'Referencia'],
    ['estimado', 'Estimado'],
  ] as const)('%s', (categoria, texto) => {
    render(<InsigniaCategoria categoria={categoria} />)
    expect(screen.getByText(texto)).toBeInTheDocument()
  })

  it('cada categoría tiene una clase distinta', () => {
    const clases = (['observado', 'referencia', 'estimado'] as const).map((c) => {
      const { container, unmount } = render(<InsigniaCategoria categoria={c} />)
      const clase = container.querySelector('.insignia')!.className
      unmount()
      return clase
    })
    expect(new Set(clases).size).toBe(3)
  })
})

describe('insignia de lectura simulada', () => {
  it('dice Simulado, con símbolo propio y distinta de las tres categorías de datos', () => {
    const { container } = render(<InsigniaSimulado />)
    expect(screen.getByText('Simulado')).toBeInTheDocument()
    expect(screen.getByText(/no de un sensor real/)).toBeInTheDocument()
    expect(container.querySelector('.insignia-simulado')).not.toBeNull()
    expect(container.querySelector('.insignia-simbolo')?.textContent).toBe('⚙')
  })
})

describe('insignias de advertencia', () => {
  it('hay una por cada una de las 6 advertencias de comparabilidad', () => {
    expect(Object.keys(ADVERTENCIAS)).toHaveLength(6)
  })

  it.each(Object.entries(ADVERTENCIAS) as [CodigoAdvertencia, { texto: string }][])(
    '%s',
    (codigo, { texto }) => {
      render(<InsigniaAdvertencia codigo={codigo} />)
      expect(screen.getByText(texto)).toBeInTheDocument()
    },
  )

  it('la cobertura baja muestra un texto corto y deja el mensaje de la API como descripción', () => {
    const mensaje =
      'Solo 40% de los días tiene dato: el acumulado puede quedar por debajo de lo que llovió.'
    const { container } = render(<InsigniaAdvertencia codigo="cobertura_baja" mensaje={mensaje} />)
    expect(screen.getByText('Cobertura baja')).toBeInTheDocument()
    expect(screen.queryByText(mensaje)).not.toBeInTheDocument()
    expect(container.querySelector('.insignia')).toHaveAttribute('title', mensaje)
  })

  it('si la API manda un mensaje, ese es el que se describe', () => {
    const { container } = render(
      <InsigniaAdvertencia codigo="ceros_prolongados" mensaje="281 días seguidos en 0 mm." />,
    )
    expect(container.querySelector('.insignia')).toHaveAttribute(
      'title',
      '281 días seguidos en 0 mm.',
    )
  })

  it('un código desconocido igual se muestra: la advertencia no se pierde', () => {
    render(<InsigniaAdvertencia codigo="regla_nueva" mensaje="Algo a revisar." />)
    expect(
      screen.getByText('Algo a revisar.', { selector: 'span:not(.sr-only)' }),
    ).toBeInTheDocument()
  })
})

describe('textoMm', () => {
  it('un hueco es «sin dato», nunca 0', () => {
    expect(textoMm(null)).toBe('sin dato')
  })

  it('un cero real sí se muestra como 0 mm', () => {
    expect(textoMm(0)).toBe('0 mm')
  })

  it('formatea con coma decimal', () => {
    expect(textoMm(12.5)).toBe('12,5 mm')
  })
})
