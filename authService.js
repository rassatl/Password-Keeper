const usersKey = "password-keeper-users";

function getUsers() {
  return JSON.parse(localStorage.getItem(usersKey) || "{}");
}

export async function registerUser(email, password) {
  const normalizedEmail = email.trim().toLowerCase();
  const users = getUsers();

  if (users[normalizedEmail]) {
    throw new Error("Un compte existe déjà avec cette adresse e-mail.");
  }

  users[normalizedEmail] = password;
  localStorage.setItem(usersKey, JSON.stringify(users));
  return { email: normalizedEmail };
}

export async function loginUser(email, password) {
  const normalizedEmail = email.trim().toLowerCase();
  const users = getUsers();

  if (users[normalizedEmail] !== password) {
    throw new Error("Adresse e-mail ou mot de passe incorrect.");
  }

  return { email: normalizedEmail };
}
