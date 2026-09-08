const currentUserKey = "password-keeper-current-user";

export async function registerUser(nom, prenom, pseudo, email, password) {
  return request("/api/auth/register", {
    nom: nom.trim(),
    prenom: prenom.trim(),
    pseudo: pseudo.trim().toLowerCase(),
    email: email.trim().toLowerCase(),
    password
  });
}

export async function loginUser(login, password) {
  const user = await request("/api/auth/login", {
    login: login.trim().toLowerCase(),
    password
  });
  localStorage.setItem(currentUserKey, JSON.stringify(user));
  return user;
}

export function getStoredUser() {
  try {
    const user = JSON.parse(localStorage.getItem(currentUserKey) || "null");
    return user?.session_token ? user : null;
  } catch {
    localStorage.removeItem(currentUserKey);
    return null;
  }
}

export function clearStoredUser() {
  localStorage.removeItem(currentUserKey);
}

export async function logoutUser() {
  await request("/api/auth/logout", undefined);
  clearStoredUser();
}

async function request(path, body, options = {}) {
  const apiBaseUrl = import.meta.env.DEV ? "" : (import.meta.env.VITE_API_URL || "");
  const storedUser = getStoredUser();
  const requestOptions = {
    method: "POST",
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(storedUser?.session_token ? { Authorization: `Bearer ${storedUser.session_token}` } : {}),
      ...(options.headers || {})
    }
  };
  if (body !== undefined) {
    requestOptions.body = JSON.stringify(body);
  }
  let response;
  try {
    response = await fetch(`${apiBaseUrl}${path}`, requestOptions);
  } catch {
    throw new Error("Impossible de joindre l'API. Lancez FastAPI sur le port 8000.");
  }

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || "Le serveur est indisponible.");
  }

  return data;
}
