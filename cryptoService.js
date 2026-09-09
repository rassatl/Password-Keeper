// Utilitaires pour convertir entre ArrayBuffer et Base64 pour le transport JSON
const bufferToBase64 = (buffer) => btoa(String.fromCharCode(...new Uint8Array(buffer)));
const base64ToBuffer = (base64) => {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes.buffer;
};

// Chiffre une chaîne en clair avec une clé (CryptoKey)
export async function encryptData(plainText, key) {
  const iv = crypto.getRandomValues(new Uint8Array(12)); // Vecteur d'initialisation unique
  const encodedData = new TextEncoder().encode(plainText);
  
  const cipherText = await crypto.subtle.encrypt(
    { name: "AES-GCM", iv },
    key,
    encodedData
  );

  // On combine l'IV (nécessaire au déchiffrement) et le texte chiffré
  const combined = new Uint8Array(iv.length + cipherText.byteLength);
  combined.set(iv, 0);
  combined.set(new Uint8Array(cipherText), iv.length);
  
  return bufferToBase64(combined.buffer); // Retourne un format compatible JSON
}

// Déchiffre une chaîne en base64 avec une clé (CryptoKey)
export async function decryptData(cipherBase64, key) {
  const encryptedBuffer = base64ToBuffer(cipherBase64);
  const encryptedBytes = new Uint8Array(encryptedBuffer);
  
  // Séparation de l'IV (les 12 premiers octets) et du texte chiffré
  const iv = encryptedBytes.slice(0, 12);
  const cipherText = encryptedBytes.slice(12);

  const decryptedBuffer = await crypto.subtle.decrypt(
    { name: "AES-GCM", iv },
    key,
    cipherText
  );

  return new TextDecoder().decode(decryptedBuffer);
}