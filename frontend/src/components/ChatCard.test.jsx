import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { jsonResponse } from '../test/fixtures'
import ChatCard from './ChatCard'

const LOCATION = { lat: 37.6199, lon: 127.063, source: 'gps' }

function mockFetch(...responses) {
  const fetchMock = vi.fn()
  responses.forEach((response) => fetchMock.mockImplementationOnce(() => response))
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

describe('ChatCard', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('질문을 보내고 답을 말풍선으로 보여 준다', async () => {
    const fetchMock = mockFetch(jsonResponse({ answer: '쌀쌀해요. 가벼운 재킷을 걸치세요.', source: 'rules' }))
    const user = userEvent.setup()
    render(<ChatCard location={LOCATION} />)

    await user.type(screen.getByLabelText('질문'), ' 오늘 뭐 입어? ')
    await user.click(screen.getByRole('button', { name: '보내기' }))

    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/chat')
    expect(JSON.parse(options.body)).toEqual({ lat: 37.6199, lon: 127.063, message: '오늘 뭐 입어?' })

    const chat = screen.getByRole('list', { name: '대화' })
    expect(within(chat).getByText('오늘 뭐 입어?')).toBeInTheDocument()
    expect(await within(chat).findByText('쌀쌀해요. 가벼운 재킷을 걸치세요.')).toBeInTheDocument()
    expect(within(chat).queryByText('AI 답')).not.toBeInTheDocument()
    expect(screen.getByLabelText('질문')).toHaveValue('')
  })

  it('source가 llm이면 AI 답 표시를 붙인다', async () => {
    mockFetch(jsonResponse({ answer: '네, 우산을 챙기세요.', source: 'llm' }))
    const user = userEvent.setup()
    render(<ChatCard location={LOCATION} />)

    await user.type(screen.getByLabelText('질문'), '우산 챙겨야 해?{Enter}')

    const answer = await screen.findByText('네, 우산을 챙기세요.')
    expect(answer).toHaveTextContent('AI 답')
  })

  it('오류가 나면 오류 말풍선을 보여 주고 다시 물을 수 있다', async () => {
    mockFetch(
      jsonResponse({ error: 'upstream_error', message: '날씨와 대기질 정보를 잠시 불러오지 못했어요.' }, 502),
      jsonResponse({ answer: '맑아요.', source: 'rules' }),
    )
    const user = userEvent.setup()
    render(<ChatCard location={LOCATION} />)

    await user.type(screen.getByLabelText('질문'), '날씨 어때?{Enter}')
    expect(await screen.findByText('날씨와 대기질 정보를 잠시 불러오지 못했어요.')).toBeInTheDocument()

    await user.type(screen.getByLabelText('질문'), '다시 알려 줘{Enter}')
    expect(await screen.findByText('맑아요.')).toBeInTheDocument()
  })

  it('위치가 없으면 입력과 보내기를 막는다', () => {
    render(<ChatCard location={null} />)

    expect(screen.getByLabelText('질문')).toBeDisabled()
    expect(screen.getByRole('button', { name: '보내기' })).toBeDisabled()
  })

  it('빈 질문은 보내지 않는다', async () => {
    const fetchMock = mockFetch()
    const user = userEvent.setup()
    render(<ChatCard location={LOCATION} />)

    await user.type(screen.getByLabelText('질문'), '   {Enter}')

    expect(fetchMock).not.toHaveBeenCalled()
  })
})
