import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it } from 'vitest'
import { loadWardrobe } from '../lib/wardrobe'
import WardrobeCard from './WardrobeCard'

describe('WardrobeCard', () => {
  beforeEach(() => localStorage.clear())

  it('옷이 없으면 안내 문구를 보여 준다', () => {
    render(<WardrobeCard />)
    expect(screen.getByText(/아직 등록한 옷이 없어요/)).toBeInTheDocument()
  })

  it('옷을 추가하면 종류별 목록에 보이고 저장된다', async () => {
    const user = userEvent.setup()
    render(<WardrobeCard />)

    await user.selectOptions(screen.getByLabelText('종류'), 'outer')
    await user.type(screen.getByLabelText('이름'), '방수 코트')
    await user.selectOptions(screen.getByLabelText('두께'), 'thick')
    await user.click(screen.getByLabelText('방수'))
    await user.click(screen.getByRole('button', { name: '추가' }))

    const list = screen.getByRole('list', { name: '겉옷 목록' })
    expect(within(list).getByText('방수 코트')).toBeInTheDocument()
    expect(within(list).getByText(/두꺼움 · 방수/)).toBeInTheDocument()
    expect(loadWardrobe()).toMatchObject([
      { category: 'outer', name: '방수 코트', thickness: 'thick', waterproof: true },
    ])
    expect(screen.getByLabelText('이름')).toHaveValue('')
  })

  it('이름이 비어 있으면 추가하지 않고 알려 준다', async () => {
    const user = userEvent.setup()
    render(<WardrobeCard />)

    await user.type(screen.getByLabelText('이름'), '   ')
    await user.click(screen.getByRole('button', { name: '추가' }))

    expect(screen.getByRole('alert')).toHaveTextContent('옷 이름을 적어 주세요.')
    expect(loadWardrobe()).toEqual([])
  })

  it('삭제 버튼을 누르면 그 옷만 지운다', async () => {
    localStorage.setItem(
      'airfit.wardrobe',
      JSON.stringify([
        { id: 'a1', category: 'top', name: '회색 니트', thickness: 'medium', waterproof: false },
        { id: 'a2', category: 'top', name: '흰 셔츠', thickness: 'thin', waterproof: false },
      ]),
    )
    const user = userEvent.setup()
    render(<WardrobeCard />)

    await user.click(screen.getByRole('button', { name: '회색 니트 삭제' }))

    expect(screen.queryByText('회색 니트')).not.toBeInTheDocument()
    expect(screen.getByText('흰 셔츠')).toBeInTheDocument()
    expect(loadWardrobe().map((item) => item.id)).toEqual(['a2'])
  })
})
