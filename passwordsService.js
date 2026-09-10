import { decryptSecret, encryptSecret } from "./vaultCrypto.js";

async function request(path, options = {}) {
  const apiBaseUrl = import.meta.env.DEV ? "" : (import.meta.env.VITE_API_URL || "");
  let response;
  try {
    response = await fetch(`${apiBaseUrl}${path}`, {
      ...options,
      credentials: "include",
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
    if (response.status === 401) {
      window.dispatchEvent(new CustomEvent("auth-expired"));
    }
    const detail = Array.isArray(data.detail)
      ? data.detail.map((error) => error.msg || "Erreur de validation").join(" ")
      : data.detail;
    throw new Error(detail || "Le serveur est indisponible.");
  }

  return data;
}

// Chaque secret est chiffré/déchiffré côté client (voir vaultCrypto.js) :
// le serveur ne reçoit et ne stocke jamais de mot de passe en clair.
async function decryptEntry(entry) {
  try {
    return { ...entry, mdp: await decryptSecret(entry.mdp) };
  } catch (error) {
    console.error("Impossible de déchiffrer cet identifiant:", error);
    return { ...entry, mdp: "", decryptionFailed: true };
  }
}

export async function getPasswords() {
  const entries = await request("/api/passwords", { method: "GET" });
  return Promise.all(entries.map(decryptEntry));
}

export async function addPasswordEntry(entry) {
  const result = await request("/api/passwords", {
    method: "POST",
    body: JSON.stringify({ ...entry, mdp: await encryptSecret(entry.mdp) })
  });
  return decryptEntry(result);
}

export async function updatePasswordEntry(id, entry) {
  const result = await request(`/api/passwords/${id}`, {
    method: "PUT",
    body: JSON.stringify({ ...entry, mdp: await encryptSecret(entry.mdp) })
  });
  return decryptEntry(result);
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
