async function request(path, options = {}) {
  const apiBaseUrl = import.meta.env.DEV ? "" : (import.meta.env.VITE_API_URL || "");
  let response;
  try {
    response = await fetch(`${apiBaseUrl}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {})
      }
    });
  } catch {
    throw new Error("Impossible de joindre l'API. Lancez FastAPI sur le port 8000.");
  }

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || "Le serveur est indisponible.");
  }

  return data;
}

export async function getPasswords(userId) {
  return request(`/api/passwords?user_id=${encodeURIComponent(userId)}`, { method: "GET" });
}