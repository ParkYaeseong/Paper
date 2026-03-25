import { existsSync, readFileSync } from 'node:fs'
import { resolve } from 'node:path'

import { describe, expect, it } from 'vitest'

describe('logout bridge', () => {
  it('exists and clears the Paper app session', () => {
    const absolutePath = resolve(process.cwd(), 'public', 'logout-bridge.html')

    expect(existsSync(absolutePath)).toBe(true)

    const source = readFileSync(absolutePath, 'utf-8')
    expect(source.includes('/api/auth/logout')).toBe(true)
    expect(source.includes('kbf:logout-bridge:complete')).toBe(true)
    expect(source.includes('postMessage')).toBe(true)
  })
})
