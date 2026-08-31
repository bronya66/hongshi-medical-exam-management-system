import { ElMessage } from 'element-plus'

const DEFAULT_FORBIDDEN_WORDS = [
  '赌博',
  '色情',
  '毒品',
  '诈骗',
  '违法',
  '暴力',
  '枪支',
  '炸弹',
  '傻逼',
  '妈的'
]

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function buildSensitiveRegex(words) {
  const safeWords = (words || [])
    .map((w) => (w || '').trim())
    .filter(Boolean)
    .sort((a, b) => b.length - a.length)

  if (!safeWords.length) {
    return null
  }

  return new RegExp(safeWords.map(escapeRegExp).join('|'), 'g')
}

export function installSensitiveInputGuard(options = {}) {
  const forbiddenWords = options.forbiddenWords || DEFAULT_FORBIDDEN_WORDS
  const replacementChar = options.replacementChar || '*'
  const messageCooldownMs = options.messageCooldownMs || 1200
  const regex = buildSensitiveRegex(forbiddenWords)

  if (!regex) {
    return () => {}
  }

  let lastWarnAt = 0

  const replaceSensitiveText = (text) => {
    if (!text || typeof text !== 'string') {
      return { changed: false, value: text }
    }

    let changed = false
    const value = text.replace(regex, (matched) => {
      changed = true
      return replacementChar.repeat(matched.length)
    })

    return { changed, value }
  }

  const warnIfNeeded = () => {
    const now = Date.now()
    if (now - lastWarnAt < messageCooldownMs) {
      return
    }
    lastWarnAt = now
    ElMessage.warning('输入内容含违规词，已自动处理')
  }

  const handleInput = (event) => {
    const target = event && event.target
    if (!target) {
      return
    }

    const tagName = (target.tagName || '').toLowerCase()
    if (tagName !== 'input' && tagName !== 'textarea') {
      return
    }

    if (tagName === 'input' && (target.type || '').toLowerCase() === 'password') {
      return
    }

    const { changed, value } = replaceSensitiveText(target.value)
    if (!changed) {
      return
    }

    target.value = value
    warnIfNeeded()

    target.dispatchEvent(new Event('input', { bubbles: true }))
  }

  document.addEventListener('input', handleInput, true)

  return () => {
    document.removeEventListener('input', handleInput, true)
  }
}
