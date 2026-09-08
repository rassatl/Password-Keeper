<script setup>
import { onMounted, onUnmounted, ref } from "vue";
import { clearStoredUser, getStoredUser, loginUser, logoutUser, registerUser } from "../authService.js";
import VaultPage from "./components/VaultPage.vue";

const status = ref({ message: "", type: "" });
const loadingAction = ref("");
const isRegistering = ref(false);
const currentUser = ref(getStoredUser());
const databaseStatus = ref({ label: "Vérification...", type: "checking" });

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
      clearStoredUser();
    } else {
      currentUser.value = await loginUser(formData.get("login"), formData.get("password"));
    }
    status.value = { message: successMessage, type: "success" };
    form.reset();
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
  clearStoredUser();
  status.value = { message: "Votre session a expiré. Veuillez vous reconnecter.", type: "error" };
  isRegistering.value = false;
}

onMounted(() => {
  checkDatabase();
  window.addEventListener("auth-expired", handleSessionExpired);
});

onUnmounted(() => {
  window.removeEventListener("auth-expired", handleSessionExpired);
});

async function logout() {
  try {
    await logoutUser();
  } catch {
    clearStoredUser();
  }
  currentUser.value = null;
  status.value = { message: "", type: "" };
}

function switchAuthMode(registering) {
  isRegistering.value = registering;
  status.value = { message: "", type: "" };
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
            <label>Mot de passe<input name="password" type="password" autocomplete="new-password" minlength="12" required /></label>
            <label>Vérifier le mot de passe<input name="passwordConfirmation" type="password" autocomplete="new-password" minlength="12" required /></label>
            <button type="submit" :disabled="loadingAction !== ''">S'inscrire</button>
            <button class="auth-switch" type="button" @click="switchAuthMode(false)">Déjà un compte ? Se connecter</button>
          </form>

          <form v-else @submit.prevent="handleSubmit('login', 'Connexion réussie.', $event)">
            <h3>Se connecter</h3>
            <label>Pseudo ou e-mail<input name="login" type="text" autocomplete="username" minlength="3" required /></label>
            <label>Mot de passe<input name="password" type="password" autocomplete="current-password" minlength="12" required /></label>
            <button type="submit" :disabled="loadingAction !== ''">Se connecter</button>
            <button class="auth-switch" type="button" @click="switchAuthMode(true)">Pas de compte ? Créer un compte</button>
          </form>
        </div>

        <p class="status" :class="status.type" role="status" aria-live="polite">{{ status.message }}</p>
      </section>
    </div>
  </main>
</template>