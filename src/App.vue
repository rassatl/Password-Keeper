<script setup>
import { onMounted, ref } from "vue";
import { loginUser, registerUser } from "../authService.js";

const status = ref({ message: "", type: "" });
const loadingAction = ref("");
const currentUser = ref(null);
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
    currentUser.value = await (action === "register"
      ? registerUser(formData.get("email"), formData.get("pseudo"), formData.get("password"))
      : loginUser(formData.get("pseudo"), formData.get("password")));
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

onMounted(checkDatabase);
</script>

<template>
  <aside v-if="currentUser" class="user-indicator" aria-live="polite">
    <strong>{{ currentUser.pseudo || "Utilisateur" }}</strong>
    <span>{{ currentUser.email }}</span>
  </aside>

  <aside class="database-indicator" :class="databaseStatus.type" aria-live="polite">
    <span class="indicator-dot" aria-hidden="true"></span>
    <span>{{ databaseStatus.label }}</span>
    <button class="refresh-button" type="button" title="Vérifier la connexion" aria-label="Vérifier la connexion" @click="checkDatabase">↻</button>
  </aside>

  <main>
    <h1>Password Keeper</h1>
    <p class="intro">Créez un compte ou connectez-vous pour accéder à votre coffre-fort.</p>

    <section class="forms" aria-label="Authentification">
      <form @submit.prevent="handleSubmit('register', 'Compte créé avec succès.', $event)">
        <h2>Créer un compte</h2>
        <label>Pseudo<input name="pseudo" type="text" autocomplete="username" minlength="3" maxlength="50" required /></label>
        <label>Adresse e-mail<input name="email" type="email" autocomplete="email" required /></label>
        <label>Mot de passe<input name="password" type="password" autocomplete="new-password" minlength="6" required /></label>
        <button type="submit" :disabled="loadingAction !== ''">S'inscrire</button>
      </form>

      <form @submit.prevent="handleSubmit('login', 'Connexion réussie.', $event)">
        <h2>Se connecter</h2>
        <label>Pseudo<input name="pseudo" type="text" autocomplete="username" minlength="3" required /></label>
        <label>Mot de passe<input name="password" type="password" autocomplete="current-password" required /></label>
        <button type="submit" :disabled="loadingAction !== ''">Se connecter</button>
      </form>
    </section>

    <p class="status" :class="status.type" role="status" aria-live="polite">{{ status.message }}</p>
  </main>
</template>