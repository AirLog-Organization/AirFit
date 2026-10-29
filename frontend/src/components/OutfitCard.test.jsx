import { render, screen, within } from '@testing-library/react'
import { expect, test } from 'vitest'
import OutfitCard from './OutfitCard'

const outfit = {
  summary: '얇은 니트에 가벼운 겉옷이 좋아요.',
  items: [
    { category: 'outer', name: '가벼운 재킷' },
    { category: 'top', name: '얇은 니트' },
    { category: 'bottom', name: '긴 바지' },
  ],
  tips: ['일교차가 7도 이상이에요. 겉옷을 챙기세요.'],
}

test('shows summary, items with category names, and tips', () => {
  render(<OutfitCard outfit={outfit} />)

  expect(screen.getByText(outfit.summary)).toBeInTheDocument()
  const items = within(screen.getByRole('list', { name: '추천 옷' })).getAllByRole('listitem')
  expect(items.map((item) => item.textContent)).toEqual([
    '겉옷가벼운 재킷',
    '상의얇은 니트',
    '하의긴 바지',
  ])
  expect(screen.getByText(outfit.tips[0])).toBeInTheDocument()
})

test('waits for the rules while the server sends null', () => {
  render(<OutfitCard outfit={null} />)

  expect(screen.getByText('옷차림 추천 규칙을 준비하고 있어요.')).toBeInTheDocument()
})
