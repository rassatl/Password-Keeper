<script setup>
import { computed, ref } from "vue";
import { getPasswords, getCategories, addPasswordEntry } from "../../passwordsService.js";

const props = defineProps({
  user: {
    type: Object,
    required: true
  }
});

const emit = defineEmits(["logout"]);

// Passwords et categories state/état
const passwords = ref([]);
const passwordsLoading = ref(true);
const passwordsError = ref("");
const showAddPassword = ref(false);
const addPasswordError = ref("");
const addPasswordLoading = ref(false);
const newPasswordSecret = ref("");

async function fetchPasswords() {
  passwordsLoading.value = true;
  passwordsError.value = "";
  try {
    const data = await getPasswords();
    passwords.value = Array.isArray(data) ? data : [];
  } catch (error) {
    passwordsError.value = error.message || "Impossible de charger les mots de passe.";
    console.error("Erreur lors de la récupération des mots de passe:", error);
  } finally {
    passwordsLoading.value = false;
  }
}

// Catégories
const password_categories = ref([]);

async function fetchCategories() {
  try {
    const data = await getCategories();
    password_categories.value = Array.isArray(data) ? data : [];
  } catch (error) {
    console.error("Erreur lors de la récupération des catégories:", error);
  }
}

// Barre latérale
const activeCategory = ref("all");
const categories = [
  { id: "all", label: "All passwords", description: "Tous vos identifiants enregistrés." },
  { id: "favorites", label: "Favorites", description: "Vos identifiants favoris." },
  { id: "work", label: "Work", description: "Vos accès professionnels." },
  { id: "personal", label: "Personal", description: "Vos accès personnels." }
];
const selectedCategory = computed(() => categories.find((category) => category.id === activeCategory.value));

function selectCategory(categoryId) {
  activeCategory.value = categoryId;
}

// Ouverture et fermeture du modal pour ajouter un mot de passe
function openAddPassword() {
  addPasswordError.value = "";
  newPasswordSecret.value = "";
  showGenerator.value = false;
  showAddPassword.value = true;
}

function closeAddPassword() {
  showAddPassword.value = false;
}

const showGenerator = ref(false);
const generatorLength = ref(16);
const generatedPassword = ref("");

const passwordStrength = computed(() => {
  const len = generatorLength.value;
  if (len < 10) return "Faible";
  if (len < 14) return "Moyen";
  return "Fort";
});

function toggleGenerator() {
  showGenerator.value = !showGenerator.value;
  if (showGenerator.value && !generatedPassword.value) {
    generatePassword();
  }
}

function generatePassword() {
  const uppers = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
  const lowers = "abcdefghijklmnopqrstuvwxyz";
  const numbers = "0123456789";
  const symbols = "!@#$%^&*()_+~`|}{[]:;?><,./-=";
  const all = uppers + lowers + numbers + symbols;

  let pwd = "";
  // On s'assure d'avoir au moins 1 caractère de chaque type pour qu'il soit "fort"
  pwd += uppers[Math.floor(Math.random() * uppers.length)];
  pwd += lowers[Math.floor(Math.random() * lowers.length)];
  pwd += numbers[Math.floor(Math.random() * numbers.length)];
  pwd += symbols[Math.floor(Math.random() * symbols.length)];

  // On complète avec des caractères aléatoires
  for (let i = 4; i < generatorLength.value; i++) {
    pwd += all[Math.floor(Math.random() * all.length)];
  }
  
  // On mélange le résultat pour ne pas toujours avoir Maj+Min+Chiffre+Symbole au début
  generatedPassword.value = pwd.split('').sort(() => 0.5 - Math.random()).join('');
}

function useGeneratedPassword() {
  newPasswordSecret.value = generatedPassword.value;
  showGenerator.value = false;
}

// Ajout du mot de passe dans le coffre-fort
async function addPassword(event) {
  const formData = new FormData(event.currentTarget);
  addPasswordLoading.value = true;
  addPasswordError.value = "";

  try {
    await addPasswordEntry({
      service: formData.get("password-form-service"),
      service_categorie: formData.get("password-form-category"),
      mdp: formData.get("password-form-secret")
    });
    await fetchPasswords();
    closeAddPassword();
  } catch (error) {
    addPasswordError.value = error.message || "Impossible d'ajouter cet identifiant.";
  } finally {
    addPasswordLoading.value = false;
  }
}

fetchPasswords();
fetchCategories();
</script>

<template>
  <div class="vault-layout">
    <aside class="vault-sidebar">
      <div class="sidebar-brand">
        <span class="brand-mark">PK</span>
        <strong>Password Keeper</strong>
      </div>
      <p class="sidebar-label">Categories</p>
      <nav aria-label="Password categories">
        <button
          v-for="category in categories"
          :key="category.id"
          class="category-link"
          :class="{ active: activeCategory === category.id }"
          type="button"
          @click="selectCategory(category.id)"
        >
          {{ category.label }}
        </button>
      </nav>
      <button class="sidebar-logout" type="button" @click="emit('logout')">Se déconnecter</button>
    </aside>

    <main class="vault-page">
      <header class="vault-header">
        <div>
          <p class="eyebrow">Espace sécurisé</p>
          <h1>{{ selectedCategory.label }}</h1>
          <p class="intro">{{ selectedCategory.description }}</p>
        </div>
        <div class="profile-block">
          <span class="avatar">{{ user.initiales || "--" }}</span>
          <div>
            <strong>{{ user.pseudo }}</strong>
            <span>{{ user.email }}</span>
          </div>
        </div>
      </header>

      <section v-if="activeCategory === 'all'" class="password-section" aria-live="polite">
        <p class="eyebrow">{{ selectedCategory.label }}</p>
        <div class="password-section-header">
          <div>
            <h2>Vos mots de passe</h2>
            <p>{{ passwords.length }} identifiant{{ passwords.length > 1 ? "s" : "" }} enregistré{{ passwords.length > 1 ? "s" : "" }}</p>
          </div>
          <button type="button" @click="openAddPassword">Ajouter un identifiant</button>
        </div>

        <p v-if="passwordsLoading" class="password-feedback">Chargement des mots de passe...</p>
        <p v-else-if="passwordsError" class="password-feedback error">{{ passwordsError }}</p>
        <p v-else-if="passwords.length === 0" class="password-feedback">Aucun mot de passe enregistré.</p>
        <div v-else class="password-list">
          <article v-for="password in passwords" :key="password.id" class="password-card">
            <div class="password-service-icon">{{ (password.service || password.name || "?").charAt(0).toUpperCase() }}</div>
            <div class="password-card-details">
              <strong>{{ password.service || password.name }}</strong>
              <span>{{ password.login || "Identifiant non renseigné" }}</span>
            </div>
            <code>{{ password.mdp || password.value }}</code>
          </article>
        </div>
      </section>

      <section v-else class="vault-empty-state" aria-live="polite">
        <p class="eyebrow">{{ selectedCategory.label }}</p>
        <h2>Aucun élément dans {{ selectedCategory.label }}</h2>
        <p>Les identifiants de cette catégorie apparaîtront ici.</p>
        <button type="button" @click="openAddPassword">Ajouter un identifiant</button>
      </section>
    </main>

    <div v-if="showAddPassword" class="modal-backdrop" @click.self="closeAddPassword">
      <section class="password-modal" role="dialog" aria-modal="true" aria-labelledby="add-password-title">
        <header class="modal-header">
          <div>
            <p class="eyebrow">Nouveau secret</p>
            <h2 id="add-password-title">Ajouter un identifiant</h2>
          </div>
          <button class="modal-close" type="button" aria-label="Fermer" @click="closeAddPassword">&times;</button>
        </header>

        <form class="password-form" autocomplete="off" @submit.prevent="addPassword">
          <label>Service<input name="password-form-service" type="text" autocomplete="off" placeholder="Ex. Netflix, GitHub..." required /></label>
          
          <label>Mot de passe
            <input 
              name="password-form-secret" 
              type="password" 
              autocomplete="new-password" 
              placeholder="Votre mot de passe" 
              v-model="newPasswordSecret"
              required 
            />
          </label>

          <!-- Bouton pour ouvrir/fermer le générateur -->
          <button type="button" class="btn-generate-toggle" @click="toggleGenerator">
            Generate Password
          </button>

          <!-- Zone du générateur -->
          <div v-if="showGenerator" class="generator-box" style="margin: 10px 0; padding: 10px; border: 1px solid #ccc; border-radius: 8px;">
            <label style="display:block; margin-bottom: 10px;">
              Longueur : <strong>{{ generatorLength }}</strong>
              <input type="range" min="8" max="64" v-model="generatorLength" @input="generatePassword" style="width: 100%;" />
            </label>
            
            <div style="background: #f4f4f4; padding: 10px; border-radius: 4px; font-family: monospace; word-break: break-all; margin-bottom: 10px;">
              {{ generatedPassword }}
            </div>
            
            <p style="margin: 0 0 10px 0; font-size: 0.9em;">
              Force du mot de passe : 
              <strong :style="{ color: passwordStrength === 'Fort' ? 'green' : passwordStrength === 'Moyen' ? 'orange' : 'red' }">
                {{ passwordStrength }}
              </strong>
            </p>

            <div style="display: flex; gap: 10px;">
              <button type="button" @click="generatePassword">Regenerate</button>
              <button type="button" @click="useGeneratedPassword">Use this password</button>
            </div>
          </div>

          <label>Catégorie
            <select name="password-form-category" required>
                <option value="">Sélectionnez une catégorie</option>
                <option v-for="category in password_categories" :key="category.id" :value="category.label">
                  {{ category.label }}
                </option>
            </select>
          </label>
          
          <label class="favorite-option"><input type="checkbox" /> Ajouter aux favoris</label>
          
          <footer class="modal-actions">
            <button class="modal-cancel" type="button" @click="closeAddPassword">Annuler</button>
            <p v-if="addPasswordError" class="password-feedback error">{{ addPasswordError }}</p>
            <button type="submit" :disabled="addPasswordLoading">{{ addPasswordLoading ? "Enregistrement..." : "Enregistrer" }}</button>
          </footer>
        </form>
      </section>
    </div>
  </div>
</template>