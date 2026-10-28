// Тексты выдуманы для учебного макета. Это не материалы Tengrinews.
export const CATEGORIES = [
  { id: 'all', label: 'Все' },
  { id: 'news', label: 'Новости' },
  { id: 'life', label: 'Life' },
  { id: 'sport', label: 'Спорт' },
  { id: 'auto', label: 'Авто' },
  { id: 'travel', label: 'Путешествия' },
]

export const CATEGORY_LABEL = Object.fromEntries(CATEGORIES.map((c) => [c.id, c.label]))

// Backwards-compatible import for the completed news fixture.
export { stories } from './data/stories';
