/**
 * Session Management for EvalGen
 * Provides anonymous, persistent 7-day browser session scoping without login.
 */

const SESSION_STORAGE_KEY = "evalgen_session_id";
const SESSION_TIMESTAMP_KEY = "evalgen_session_created_at";

function generateSessionId(): string {
  const rand = Math.random().toString(36).substring(2, 10);
  const time = Date.now().toString(36);
  return `sess_${time}_${rand}`;
}

export function getSessionId(maxAgeDays: number = 7): string {
  if (typeof window === "undefined" || !window.localStorage) {
    return "anonymous";
  }

  try {
    const existingId = localStorage.getItem(SESSION_STORAGE_KEY);
    const createdAtStr = localStorage.getItem(SESSION_TIMESTAMP_KEY);
    const now = Date.now();
    const maxAgeMs = maxAgeDays * 24 * 60 * 60 * 1000;

    if (existingId && createdAtStr) {
      const createdAt = parseInt(createdAtStr, 10);
      if (!isNaN(createdAt) && now - createdAt < maxAgeMs) {
        return existingId;
      }
    }

    // Initialize or rotate expired session
    const newSessionId = generateSessionId();
    localStorage.setItem(SESSION_STORAGE_KEY, newSessionId);
    localStorage.setItem(SESSION_TIMESTAMP_KEY, now.toString());
    return newSessionId;
  } catch (e) {
    console.warn("Could not access localStorage for session id:", e);
    return "anonymous";
  }
}

export function resetSession(): string {
  if (typeof window === "undefined" || !window.localStorage) {
    return "anonymous";
  }
  const newSessionId = generateSessionId();
  localStorage.setItem(SESSION_STORAGE_KEY, newSessionId);
  localStorage.setItem(SESSION_TIMESTAMP_KEY, Date.now().toString());
  return newSessionId;
}

export function getSessionCreatedDate(): Date | null {
  if (typeof window === "undefined" || !window.localStorage) return null;
  const createdAtStr = localStorage.getItem(SESSION_TIMESTAMP_KEY);
  if (!createdAtStr) return null;
  const time = parseInt(createdAtStr, 10);
  return isNaN(time) ? null : new Date(time);
}
