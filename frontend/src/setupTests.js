import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

// vitest globals를 켜지 않아 Testing Library가 자동으로 정리하지 않는다
afterEach(cleanup)
