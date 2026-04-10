const isInternalPath = (value) => typeof value === 'string' && value.startsWith('/') && !value.startsWith('//')

export const getReferrerPath = (currentPath = '') => {
  const historyBack = window.history?.state?.back
  if (isInternalPath(historyBack) && historyBack !== currentPath) {
    return historyBack
  }

  const rawReferrer = String(document.referrer || '').trim()
  if (!rawReferrer) return ''

  try {
    const parsed = new URL(rawReferrer)
    if (parsed.origin !== window.location.origin) return ''

    const referrerPath = `${parsed.pathname}${parsed.search}${parsed.hash}`
    if (isInternalPath(referrerPath) && referrerPath !== currentPath) {
      return referrerPath
    }
  } catch {
    return ''
  }

  return ''
}

export const navigateBack = (router, fallbackTarget, currentPath = '') => {
  const referrerPath = getReferrerPath(currentPath)
  if (referrerPath) {
    router.back()
    return
  }

  router.push(fallbackTarget)
}
