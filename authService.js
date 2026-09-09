import { lockVault, unlockVault } from "./vaultCrypto.js";

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
  await unlockVault(password, user.kdf_salt);
  return user;
}

// Le token de session vit dans un cookie httpOnly géré par le navigateur ;
// on interroge le serveur pour savoir si une session est toujours active.
// Ce n'est pas une vraie déconnexion si l'appel échoue au premier chargement,
// donc on n'utilise pas request() (qui déclenche l'évènement "session expirée").
export async function fetchCurrentUser() {
  const apiBaseUrl = import.meta.env.DEV ? "" : (import.meta.env.VITE_API_URL || "");
  try {
    const response = await fetch(`${apiBaseUrl}/api/auth/me`, { credentials: "include" });
    if (!response.ok) {
      return null;
    }
    return await response.json();
  } catch {
    return null;
  }
}

export async function unlockVaultWithPassword(password, kdfSalt) {
  await unlockVault(password, kdfSalt);
}

export function notifySessionExpired() {
  lockVault();
  window.dispatchEvent(new CustomEvent("auth-expired"));
}

export async function logoutUser() {
  try {
    await request("/api/auth/logout", undefined);
  } finally {
    lockVault();
  }
}

async function request(path, body, options = {}) {
  const apiBaseUrl = import.meta.env.DEV ? "" : (import.meta.env.VITE_API_URL || "");
  const requestOptions = {
    method: "POST",
    credentials: "include",
    ...options,
    headers: {
      "Content-Type": "application/json",
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
    if (response.status === 401) {
      notifySessionExpired();
    }
    throw new Error(data.detail || "Le serveur est indisponible.");
  }

  return data;
}
