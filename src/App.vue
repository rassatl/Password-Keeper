<script setup>
import { ref } from "vue";
import { loginUser, registerUser } from "../authService.js";

const status = ref({ message: "", type: "" });
const loadingAction = ref("");

async function handleSubmit(action, successMessage, event) {
  const form = event.target;
  const formData = new FormData(form);
  loadingAction.value = action;
  status.value = { message: "Traitement en cours...", type: "" };

  try {
    await (action === "register"
      ? registerUser(formData.get("email"), formData.get("password"))
      : loginUser(formData.get("email"), formData.get("password")));
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
</script>

<template>
  <main>
    <h1>Password Keeper</h1>
    <p class="intro">Créez un compte ou connectez-vous pour accéder à votre coffre-fort.</p>

    <section class="forms" aria-label="Authentification">
      <form @submit.prevent="handleSubmit('register', 'Compte créé avec succès.', $event)">
        <h2>Créer un compte</h2>
        <label>Adresse e-mail<input name="email" type="email" autocomplete="email" required /></label>
        <label>Mot de passe<input name="password" type="password" autocomplete="new-password" minlength="6" required /></label>
        <button type="submit" :disabled="loadingAction !== ''">S'inscrire</button>
      </form>

      <form @submit.prevent="handleSubmit('login', 'Connexion réussie.', $event)">
        <h2>Se connecter</h2>
        <label>Adresse e-mail<input name="email" type="email" autocomplete="email" required /></label>
        <label>Mot de passe<input name="password" type="password" autocomplete="current-password" required /></label>
        <button type="submit" :disabled="loadingAction !== ''">Se connecter</button>
      </form>
    </section>

    <p class="status" :class="status.type" role="status" aria-live="polite">{{ status.message }}</p>
  </main>
</template>