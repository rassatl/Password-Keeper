// Chiffrement "zero-knowledge" du coffre : la clé est dérivée du mot de passe
// maître de l'utilisateur, entièrement côté client (WebCrypto), et n'est
// jamais envoyée au serveur. Le serveur ne voit et ne stocke que le blob
// chiffré retourné par encryptSecret().
const KDF_ITERATIONS = 210_000;

let vaultKey = null;

function hexToBytes(hex) {
  const bytes = new Uint8Array(hex.length / 2);
  for (let i = 0; i < bytes.length; i++) {
    bytes[i] = parseInt(hex.substr(i * 2, 2), 16);
  }
  return bytes;
}

function bytesToBase64(bytes) {
  let binary = "";
  for (const byte of bytes) {
    binary += String.fromCharCode(byte);
  }
  return btoa(binary);
}

function base64ToBytes(base64) {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

async function deriveKeyFromPassword(password, saltHex) {
  const baseKey = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(password),
    "PBKDF2",
    false,
    ["deriveKey"]
  );
  return crypto.subtle.deriveKey(
    { name: "PBKDF2", salt: hexToBytes(saltHex), iterations: KDF_ITERATIONS, hash: "SHA-256" },
    baseKey,
    { name: "AES-GCM", length: 256 },
    false,
    ["encrypt", "decrypt"]
  );
}

export async function unlockVault(password, kdfSalt) {
  if (!kdfSalt) {
    throw new Error("Clé de coffre introuvable pour cet utilisateur.");
  }
  vaultKey = await deriveKeyFromPassword(password, kdfSalt);
}

export function lockVault() {
  vaultKey = null;
}

export function isVaultUnlocked() {
  return vaultKey !== null;
}

export async function encryptSecret(plainText) {
  if (!vaultKey) {
    throw new Error("Le coffre est verrouillé. Ressaisissez votre mot de passe maître.");
  }
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const cipherBuffer = await crypto.subtle.encrypt(
    { name: "AES-GCM", iv },
    vaultKey,
    new TextEncoder().encode(plainText)
  );
  return `v1:${bytesToBase64(iv)}:${bytesToBase64(new Uint8Array(cipherBuffer))}`;
}

export async function decryptSecret(blob) {
  if (!vaultKey) {
    throw new Error("Le coffre est verrouillé. Ressaisissez votre mot de passe maître.");
  }
  const parts = blob.split(":");
  if (parts.length !== 3 || parts[0] !== "v1") {
    throw new Error("Format de secret non reconnu.");
  }
  const iv = base64ToBytes(parts[1]);
  const cipherBytes = base64ToBytes(parts[2]);
  const plainBuffer = await crypto.subtle.decrypt({ name: "AES-GCM", iv }, vaultKey, cipherBytes);
  return new TextDecoder().decode(plainBuffer);
}
