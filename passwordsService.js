async function request(path, options = {}) {
  const apiBaseUrl = import.meta.env.DEV ? "" : (import.meta.env.VITE_API_URL || "");
  let response;
  try {
    response = await fetch(`${apiBaseUrl}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(getSessionToken() ? { Authorization: `Bearer ${getSessionToken()}` } : {}),
        ...(options.headers || {})
      }
    });
  } catch {
    throw new Error("Impossible de joindre l'API. Lancez FastAPI sur le port 8000.");
  }

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (response.status === 401) {
      localStorage.removeItem("password-keeper-current-user");
      window.dispatchEvent(new CustomEvent("auth-expired"));
    }
    const detail = Array.isArray(data.detail)
      ? data.detail.map((error) => error.msg || "Erreur de validation").join(" ")
      : data.detail;
    throw new Error(detail || "Le serveur est indisponible.");
  }

  return data;
}

function getSessionToken() {
  try {
    return JSON.parse(localStorage.getItem("password-keeper-current-user") || "null")?.session_token;
  } catch {
    return null;
  }
}

export async function getPasswords() {
  return request("/api/passwords", { method: "GET" });
}

export async function addPasswordEntry(entry) {
  return request("/api/passwords", {
    method: "POST",
    body: JSON.stringify(entry)
  });
}

export async function updatePasswordEntry(id, entry) {
  return request(`/api/passwords/${id}`, {
    method: "PUT",
    body: JSON.stringify(entry)
  });
}

export async function getCategories() {
  return request("/api/categories", { method: "GET" });
}

export async function addCategory(category) {
  return request("/api/categories", {
    method: "POST",
    body: JSON.stringify(category)
  });
}