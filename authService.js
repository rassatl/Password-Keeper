export async function registerUser(email, pseudo, password) {
  return request("/api/auth/register", {
    email: email.trim().toLowerCase(),
    pseudo: pseudo.trim().toLowerCase(),
    password
  });
}

export async function loginUser(pseudo, password) {
  return request("/api/auth/login", {
    pseudo: pseudo.trim().toLowerCase(),
    password
  });
}

async function request(path, body) {
  const apiBaseUrl = import.meta.env.DEV ? "" : (import.meta.env.VITE_API_URL || "");
  let response;
  try {
    response = await fetch(`${apiBaseUrl}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
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
