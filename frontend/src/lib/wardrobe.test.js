import { beforeEach, describe, expect, it } from 'vitest'
import { addItem, loadWardrobe, removeItem, updateItem } from './wardrobe'

const KNIT = { category: 'top', name: '회색 니트', thickness: 'medium', waterproof: false }
const COAT = { category: 'outer', name: '방수 코트', thickness: 'thick', waterproof: true }

describe('wardrobe', () => {
  beforeEach(() => localStorage.clear())

  it('저장된 옷이 없으면 빈 목록을 돌려준다', () => {
    expect(loadWardrobe()).toEqual([])
  })

  it('옷을 추가하면 id를 붙여 목록 끝에 넣고 저장한다', () => {
    const items = addItem(addItem([], KNIT), COAT)

    expect(items.map((item) => item.name)).toEqual(['회색 니트', '방수 코트'])
    expect(typeof items[0].id).toBe('string')
    expect(items[0].id).not.toBe(items[1].id)
    expect(loadWardrobe()).toEqual(items)
  })

  it('이름 앞뒤 공백은 지우고 저장한다', () => {
    const [item] = addItem([], { ...KNIT, name: '  회색 니트 ' })
    expect(item.name).toBe('회색 니트')
  })

  it('추가할 때 원래 목록은 바꾸지 않는다', () => {
    const before = addItem([], KNIT)
    addItem(before, COAT)
    expect(before).toHaveLength(1)
  })

  it('id가 같은 옷만 지우고 저장한다', () => {
    const items = addItem(addItem([], KNIT), COAT)
    const left = removeItem(items, items[0].id)

    expect(left.map((item) => item.name)).toEqual(['방수 코트'])
    expect(loadWardrobe()).toEqual(left)
  })

  it('저장값이 깨졌으면 빈 목록, 모양이 틀린 옷은 빼고 읽는다', () => {
    localStorage.setItem('airfit.wardrobe', '{깨진 값')
    expect(loadWardrobe()).toEqual([])

    const good = { id: 'a1', ...KNIT }
    localStorage.setItem(
      'airfit.wardrobe',
      JSON.stringify([good, { id: 'a2', category: 'hat', name: '모자', thickness: 'thin', waterproof: false }]),
    )
    expect(loadWardrobe()).toEqual([good])
  })

  it('수정하면 id와 순서는 그대로 두고 값만 바꿔 저장한다', () => {
    const items = addItem(addItem([], KNIT), COAT)
    const edited = updateItem(items, items[0].id, { ...KNIT, name: ' 검정 니트 ', thickness: 'thick' })

    expect(edited.map((item) => item.name)).toEqual(['검정 니트', '방수 코트'])
    expect(edited[0]).toMatchObject({ id: items[0].id, thickness: 'thick' })
    expect(edited[1]).toBe(items[1])
    expect(loadWardrobe()).toEqual(edited)
  })
})
