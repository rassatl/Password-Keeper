<script setup>
import { onMounted, onUnmounted, ref } from "vue";
import { fetchCurrentUser, loginUser, logoutUser, registerUser } from "../authService.js";
import { lockVault } from "../vaultCrypto.js";
import VaultPage from "./components/VaultPage.vue";

const status = ref({ message: "", type: "" });
const loadingAction = ref("");
const isRegistering = ref(false);
const currentUser = ref(null);
const databaseStatus = ref({ label: "Vérification...", type: "checking" });

// Variables pour gérer la visibilité des mots de passe
const showRegisterPassword = ref(false);
const showRegisterPasswordConfirm = ref(false);
const showLoginPassword = ref(false);

async function checkDatabase() {
  databaseStatus.value = { label: "Vérification...", type: "checking" };
  try {
    const apiBaseUrl = import.meta.env.DEV ? "" : (import.meta.env.VITE_API_URL || "");
    const response = await fetch(`${apiBaseUrl}/api/health`);
    const data = await response.json();
    if (!response.ok || data.database !== "connected") {
      throw new Error();
    }
    databaseStatus.value = { label: "BDD connectée", type: "online" };
  } catch {
    databaseStatus.value = { label: "BDD indisponible", type: "offline" };
  }
}

async function handleSubmit(action, successMessage, event) {
  const form = event.target;
  const formData = new FormData(form);
  loadingAction.value = action;
  status.value = { message: "Traitement en cours...", type: "" };

  try {
    if (action === "register") {
      const password = formData.get("password");
      const passwordConfirmation = formData.get("passwordConfirmation");
      if (password !== passwordConfirmation) {
        throw new Error("Les mots de passe ne correspondent pas.");
      }
      await registerUser(
        formData.get("nom"),
        formData.get("prenom"),
        formData.get("pseudo"),
        formData.get("email"),
        password
      );
      currentUser.value = null;
      isRegistering.value = false;
    } else {
      currentUser.value = await loginUser(formData.get("login"), formData.get("password"));
    }
    status.value = { message: successMessage, type: "success" };
    form.reset();
    
    showRegisterPassword.value = false;
    showRegisterPasswordConfirm.value = false;
    showLoginPassword.value = false;
    
  } catch (error) {
    status.value = {
      message: error.message || "Une erreur est survenue.",
      type: "error"
    };
  } finally {
    loadingAction.value = "";
  }
}

function handleSessionExpired() {
  currentUser.value = null;
  lockVault();
  status.value = { message: "Votre session a expiré. Veuillez vous reconnecter.", type: "error" };
  isRegistering.value = false;
}

onMounted(async () => {
  checkDatabase();
  currentUser.value = await fetchCurrentUser();
  window.addEventListener("auth-expired", handleSessionExpired);
});

onUnmounted(() => {
  window.removeEventListener("auth-expired", handleSessionExpired);
});

async function logout() {
  await logoutUser();
  currentUser.value = null;
  status.value = { message: "", type: "" };
}

function switchAuthMode(registering) {
  isRegistering.value = registering;
  status.value = { message: "", type: "" };
  
  showRegisterPassword.value = false;
  showRegisterPasswordConfirm.value = false;
  showLoginPassword.value = false;
}
</script>

<template>
  <aside class="database-indicator" :class="databaseStatus.type" aria-live="polite">
    <span class="indicator-dot" aria-hidden="true"></span>
    <span>{{ databaseStatus.label }}</span>
    <button class="refresh-button" type="button" title="Vérifier la connexion" aria-label="Vérifier la connexion" @click="checkDatabase">↻</button>
  </aside>

  <VaultPage v-if="currentUser" :user="currentUser" @logout="logout" />

  <main v-else class="auth-page">
    <div class="auth-shell">
      <section class="auth-brand" aria-label="Password Keeper">
        <div class="brand-mark large">PK</div>
        <p class="brand-kicker">Password Keeper</p>
        <h1>Vos accès, enfin bien rangés.</h1>
        <p class="brand-copy">Un espace calme pour retrouver vos identifiants importants, au bon endroit.</p>
        <div class="brand-line"></div>
        <span class="brand-caption">Private by design</span>
      </section>

      <section class="auth-content" aria-label="Authentification">
        <div class="auth-heading">
          <p class="eyebrow">Espace sécurisé</p>
          <h2>Bienvenue</h2>
          <p class="intro">{{ isRegistering ? "Quelques informations pour commencer." : "Retrouvez votre coffre-fort." }}</p>
        </div>

        <div class="forms single-form">
          <form v-if="isRegistering" @submit.prevent="handleSubmit('register', 'Compte créé avec succès.', $event)">
            <h3>Créer un compte</h3>
            <label>Nom<input name="nom" type="text" autocomplete="family-name" maxlength="50" required /></label>
            <label>Prénom<input name="prenom" type="text" autocomplete="given-name" maxlength="50" required /></label>
            <label>Pseudo<input name="pseudo" type="text" autocomplete="username" minlength="3" maxlength="50" required /></label>
            <label>Adresse e-mail<input name="email" type="email" autocomplete="email" required /></label>
            
            <label>Mot de passe
              <div class="password-wrapper">
                <input name="password" :type="showRegisterPassword ? 'text' : 'password'" autocomplete="new-password" minlength="12" required />
                <button type="button" class="toggle-password-btn" @click="showRegisterPassword = !showRegisterPassword" :title="showRegisterPassword ? 'Cacher le mot de passe' : 'Afficher le mot de passe'">
                  <svg v-if="showRegisterPassword" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9.88 9.88a3 3 0 1 0 4.24 4.24"/><path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68"/><path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61"/><line x1="2" x2="22" y1="2" y2="22"/></svg>
                  <svg v-else xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>
                </button>
              </div>
            </label>
            
            <label>Vérifier le mot de passe
              <div class="password-wrapper">
                <input name="passwordConfirmation" :type="showRegisterPasswordConfirm ? 'text' : 'password'" autocomplete="new-password" minlength="12" required />
                <button type="button" class="toggle-password-btn" @click="showRegisterPasswordConfirm = !showRegisterPasswordConfirm" :title="showRegisterPasswordConfirm ? 'Cacher le mot de passe' : 'Afficher le mot de passe'">
                  <svg v-if="showRegisterPasswordConfirm" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9.88 9.88a3 3 0 1 0 4.24 4.24"/><path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68"/><path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61"/><line x1="2" x2="22" y1="2" y2="22"/></svg>
                  <svg v-else xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>
                </button>
              </div>
            </label>
            
            <button type="submit" :disabled="loadingAction !== ''">S'inscrire</button>
            <button class="auth-switch" type="button" @click="switchAuthMode(false)">Déjà un compte ? Se connecter</button>
          </form>

          <form v-else @submit.prevent="handleSubmit('login', 'Connexion réussie.', $event)">
            <h3>Se connecter</h3>
            <label>Pseudo ou e-mail<input name="login" type="text" autocomplete="username" minlength="3" required /></label>
            
            <label>Mot de passe
              <div class="password-wrapper">
                <input name="password" :type="showLoginPassword ? 'text' : 'password'" autocomplete="current-password" minlength="12" required />
                <button type="button" class="toggle-password-btn" @click="showLoginPassword = !showLoginPassword" :title="showLoginPassword ? 'Cacher le mot de passe' : 'Afficher le mot de passe'">
                  <svg v-if="showLoginPassword" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9.88 9.88a3 3 0 1 0 4.24 4.24"/><path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68"/><path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61"/><line x1="2" x2="22" y1="2" y2="22"/></svg>
                  <svg v-else xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>
                </button>
              </div>
            </label>
            
            <button type="submit" :disabled="loadingAction !== ''">Se connecter</button>
            <button class="auth-switch" type="button" @click="switchAuthMode(true)">Pas de compte ? Créer un compte</button>
          </form>
        </div>

        <p class="status" :class="status.type" role="status" aria-live="polite">{{ status.message }}</p>
      </section>
    </div>
  </main>
</template>