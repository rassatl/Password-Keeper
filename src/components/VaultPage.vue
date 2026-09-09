<script setup>
import { computed, ref } from "vue";
import { getPasswords, getCategories, addPasswordEntry, addCategory, updatePasswordEntry } from "../../passwordsService.js";

const props = defineProps({
  user: {
    type: Object,
    required: true
  }
});

const emit = defineEmits(["logout"]);

// Passwords et categories state/état
const passwords = ref([]);
const favoritePasswords = ref([]);
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
    favoritePasswords.value = passwords.value.filter((password) => password.favori);
  } catch (error) {
    passwordsError.value = error.message || "Impossible de charger les mots de passe.";
    console.error("Erreur lors de la récupération des mots de passe:", error);
  } finally {
    passwordsLoading.value = false;
  }
}

// Édition d'un identifiant existant
const showEditPassword = ref(false);
const editPasswordError = ref("");
const editPasswordLoading = ref(false);
const editingPassword = ref(null);
const showEditSecret = ref(false);

function openEditPassword(password) {
  editPasswordError.value = "";
  editingPassword.value = { ...password };
  showEditSecret.value = false;
  showEditPassword.value = true;
}

function closeEditPassword() {
  showEditPassword.value = false;
  editingPassword.value = null;
  showEditSecret.value = false;
}

async function editPassword(event) {
  const formData = new FormData(event.currentTarget);
  editPasswordLoading.value = true;
  editPasswordError.value = "";

  try {
    await updatePasswordEntry(editingPassword.value.id, {
      identifiant: formData.get("edit-password-form-identifier"),
      service: formData.get("edit-password-form-service"),
      url_service: formData.get("edit-password-form-url-service"),
      service_categorie: formData.get("edit-password-form-category"),
      favori: formData.get("edit-password-form-favorite") === "on",
      mdp: formData.get("edit-password-form-secret"),
      mdp_force: passwordStrength.value
    });
    await fetchPasswords();
    closeEditPassword();
  } catch (error) {
    editPasswordError.value = error.message || "Impossible de modifier cet identifiant.";
  } finally {
    editPasswordLoading.value = false;
  }
}

// Gestion de la visibilité des mots de passe affichés dans les listes
const visiblePasswordIds = ref(new Set());

function togglePasswordVisibility(id) {
  if (visiblePasswordIds.value.has(id)) {
    visiblePasswordIds.value.delete(id);
  } else {
    visiblePasswordIds.value.add(id);
  }
}

function isPasswordVisible(id) {
  return visiblePasswordIds.value.has(id);
}

// Catégories
const showAddCategory = ref(false);
const addCategoryLoading = ref(false);
const addCategoryError = ref("");

const newCategoryName = ref("");
const newCategoryDescription = ref("");
const categories = ref([
  { id_categorie: "tout", nom: "Tout les identifiants", description: "Tous vos identifiants enregistrés." },
  { id_categorie: "favoris", nom: "Favoris", description: "Vos identifiants favoris." }
]);

async function fetchCategories() {
  try {
    const data = await getCategories();
    categories.value = [
      { id_categorie: "tout", nom: "Tout les identifiants", description: "Tous vos identifiants enregistrés." },
      { id_categorie: "favoris", nom: "Favoris", description: "Vos identifiants favoris." },
      ...(Array.isArray(data) ? data : [])
    ];
  } catch (error) {
    console.error("Erreur lors de la récupération des catégories:", error);
  }
}

function openAddCategory() {
  addCategoryError.value = "";
  newCategoryName.value = "";
  newCategoryDescription.value = "";
  showAddCategory.value = true;
}

function closeAddCategory() {
  showAddCategory.value = false;
}

async function createCategory() {
  addCategoryLoading.value = true;
  addCategoryError.value = "";

  try {
    await addCategory({
      nom: newCategoryName.value.trim(),
      description: newCategoryDescription.value.trim()
    });

    await fetchCategories();

    closeAddCategory();
  } catch (error) {
    addCategoryError.value =
      error.message || "Impossible de créer la catégorie.";
  } finally {
    addCategoryLoading.value = false;
  }
}

// Barre latérale
const activeCategory = ref("tout");
const selectedCategory = computed(() => {
  return categories.value.find(
    (category) => category.id_categorie === activeCategory.value
  ) ?? {
    nom: "Catégorie inconnue",
    description: ""
  };
});

const visiblePasswords = computed(() => {
  if (activeCategory.value === "favoris") {
    return favoritePasswords.value;
  }

  if (activeCategory.value === "tout") {
    return passwords.value;
  }

  return passwords.value.filter(
    (password) => password.service_categorie === selectedCategory.value.nom
  );
});

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

// Fonction faite a l'aide d'internet
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
      identifiant: formData.get("password-form-identifier"),
      service: formData.get("password-form-service"),
      url_service: formData.get("password-form-url-service"),
      service_categorie: formData.get("password-form-category"),
      favori: formData.get("password-form-favorite") === "on",
      mdp: formData.get("password-form-secret"),
      mdp_force: passwordStrength.value
    });
    await fetchPasswords();
    closeAddPassword();
  } catch (error) {
    addPasswordError.value = error.message || "Impossible d'ajouter cet identifiant.";
  } finally {
    addPasswordLoading.value = false;
  }
}

// Copie du mot de passe dans le presse-papiers
const copiedPasswordId = ref(null);

async function copyPassword(password) {
  const value = password.mdp || password.value || "";
  try {
    await navigator.clipboard.writeText(value);
    copiedPasswordId.value = password.id;
    setTimeout(() => {
      if (copiedPasswordId.value === password.id) {
        copiedPasswordId.value = null;
      }
    }, 1500);
  } catch (error) {
    console.error("Erreur lors de la copie du mot de passe:", error);
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
        <button v-for="category in categories" :key="category.id_categorie" class="category-link"
          :class="{ active: activeCategory === category.id_categorie }" type="button"
          @click="selectCategory(category.id_categorie)">
          {{ category.nom }}
        </button>
      </nav>
      <button class="sidebar-logout" type="button" @click="emit('logout')">Se déconnecter</button>
    </aside>

    <main class="vault-page">
      <header class="vault-header">
        <div>
          <p class="eyebrow">Espace sécurisé</p>
          <h1>{{ selectedCategory.nom }}</h1>
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

      <!-- Section "Tout" / "Favoris" / Catégorie -->
      <section v-if="visiblePasswords.length > 0 || activeCategory === 'tout' || activeCategory === 'favoris'"
        class="password-section" aria-live="polite">
        <p class="eyebrow">{{ selectedCategory.nom }}</p>
        <div class="password-section-header">
          <div>
            <h2>Vos mots de passe</h2>
            <p>{{ visiblePasswords.length }} identifiant{{ visiblePasswords.length > 1 ? "s" : "" }} enregistré{{
              visiblePasswords.length > 1 ? "s" : "" }}</p>
          </div>
          <button type="button" @click="openAddPassword">Ajouter un identifiant</button>
        </div>

        <p v-if="passwordsLoading" class="password-feedback">Chargement des mots de passe...</p>
        <p v-else-if="passwordsError" class="password-feedback error">{{ passwordsError }}</p>
        <p v-else-if="visiblePasswords.length === 0" class="password-feedback">Aucun mot de passe enregistré.</p>
        <div v-else class="password-list">
          <article v-for="password in visiblePasswords" :key="password.id" class="password-card">
            <div class="password-service-icon">{{ (password.service || password.name || "?").charAt(0).toUpperCase() }}
            </div>
            <div class="password-card-details">
              <strong>{{ password.service || password.name }}</strong>
              <span>{{ password.service_categorie || "Catégorie non renseignée" }}</span>
              <span>{{ password.identifiant || "Identifiant non renseigné" }}</span>
            </div>
            <div class="password-wrapper password-display">
              <code>{{ isPasswordVisible(password.id) ? (password.mdp || password.value) : '••••••••••' }}</code>
              <button type="button" class="toggle-password-btn" @click="togglePasswordVisibility(password.id)"
                :title="isPasswordVisible(password.id) ? 'Cacher le mot de passe' : 'Afficher le mot de passe'">
                <svg v-if="isPasswordVisible(password.id)" xmlns="http://www.w3.org/2000/svg" width="18" height="18"
                  viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
                  stroke-linejoin="round">
                  <path d="M9.88 9.88a3 3 0 1 0 4.24 4.24" />
                  <path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68" />
                  <path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61" />
                  <line x1="2" x2="22" y1="2" y2="22" />
                </svg>
                <svg v-else xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none"
                  stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z" />
                  <circle cx="12" cy="12" r="3" />
                </svg>
              </button>
              <button type="button" class="toggle-password-btn" @click="copyPassword(password)"
                :title="copiedPasswordId === password.id ? 'Copié !' : 'Copier le mot de passe'">
                <svg v-if="copiedPasswordId === password.id" xmlns="http://www.w3.org/2000/svg" width="18" height="18"
                  viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
                  stroke-linejoin="round">
                  <path d="M20 6 9 17l-5-5" />
                </svg>
                <svg v-else xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none"
                  stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                  <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                </svg>
              </button>
              <button type="button" class="toggle-password-btn" @click="openEditPassword(password)"
                title="Modifier cet identifiant">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none"
                  stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z" />
                </svg>
              </button>
            </div>
            <div class="password-service-mdp-strength">
              <strong
                :style="{ color: password.mdp_force === 'Fort' ? 'green' : password.mdp_force === 'Moyen' ? 'orange' : 'red' }">
                {{ password.mdp_force }}
              </strong>
            </div>
          </article>
        </div>
      </section>

      <!-- Section par défaut-->
      <section v-else class="vault-empty-state" aria-live="polite">
        <p class="eyebrow">{{ selectedCategory.nom }}</p>
        <h2>Aucun élément dans {{ selectedCategory.nom }}</h2>
        <p>Les identifiants de cette catégorie apparaîtront ici.</p>
        <button type="button" @click="openAddPassword">Ajouter un identifiant</button>
      </section>
    </main>

    <section v-if="showEditPassword" class="password-modal" role="dialog" aria-modal="true"
      aria-labelledby="edit-password-title" style="position: fixed; inset: 0; margin: auto; height: fit-content;">
      <header class="modal-header">
        <div>
          <p class="eyebrow">Modifier le secret</p>
          <h2 id="edit-password-title">Modifier un identifiant</h2>
        </div>
        <button class="modal-close" type="button" aria-label="Fermer" @click="closeEditPassword">&times;</button>
      </header>

      <form class="password-form" autocomplete="off" @submit.prevent="editPassword">
        <label>Service<input name="edit-password-form-service" type="text" autocomplete="off"
            :value="editingPassword?.service" required /></label>

        <label>URL du service<input name="edit-password-form-url-service" type="url" autocomplete="off"
            :value="editingPassword?.url_service" required /></label>

        <label>Identifiant (login ou email)<input name="edit-password-form-identifier" type="text" autocomplete="off"
            :value="editingPassword?.identifiant" required /></label>

        <label>Mot de passe
          <div class="password-wrapper">
            <input name="edit-password-form-secret" :type="showEditSecret ? 'text' : 'password'" minlength="8" maxlength="64"
              autocomplete="new-password" :value="editingPassword?.mdp" required />
            <button type="button" class="toggle-password-btn" @click="showEditSecret = !showEditSecret"
              :title="showEditSecret ? 'Cacher le mot de passe' : 'Afficher le mot de passe'">
              <svg v-if="showEditSecret" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9.88 9.88a3 3 0 1 0 4.24 4.24"/><path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68"/><path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61"/><line x1="2" x2="22" y1="2" y2="22"/></svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>
            </button>
          </div>
        </label>

        <label>Catégorie
          <select name="edit-password-form-category" required>
            <option value="">Sélectionnez une catégorie</option>
            <option
              v-for="category in categories.filter(c => c.id_categorie !== 'tout' && c.id_categorie !== 'favoris')"
              :key="category.id_categorie" :value="category.nom"
              :selected="category.nom === editingPassword?.service_categorie">
              {{ category.nom }}
            </option>
          </select>
        </label>

        <label class="favorite-option">
          <input type="checkbox" name="edit-password-form-favorite" :checked="editingPassword?.favori" /> Ajouter aux
          favoris
        </label>

        <footer class="modal-actions">
          <button class="modal-cancel" type="button" @click="closeEditPassword">Annuler</button>
          <p v-if="editPasswordError" class="password-feedback error">{{ editPasswordError }}</p>
          <button type="submit" :disabled="editPasswordLoading">{{ editPasswordLoading ? "Enregistrement..." :
            "Enregistrer" }}</button>
        </footer>
      </form>
    </section>

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
          <label>Service<input name="password-form-service" type="text" autocomplete="off"
              placeholder="Ex. Netflix, GitHub..." required /></label>

          <label>URL du service<input name="password-form-url-service" type="url" autocomplete="off"
              placeholder="Ex. https://www.netflix.com..." required /></label>

          <label>Identifiant (login ou email)<input name="password-form-identifier" type="text" autocomplete="off"
              placeholder="Ex. JohnDoe ou john.doe@example.com..." required /></label>

          <label>Mot de passe
            <input name="password-form-secret" type="password" minlength="8" maxlength="64" autocomplete="new-password"
              placeholder="Votre mot de passe" v-model="newPasswordSecret" required />
          </label>

          <!-- Bouton pour ouvrir/fermer le générateur -->
          <button type="button" class="btn-generate-toggle" @click="toggleGenerator">
            Générer un mot de passe
          </button>

          <!-- Zone du générateur -->
          <div v-if="showGenerator" class="generator-box"
            style="margin: 10px 0; padding: 10px; border: 1px solid #ccc; border-radius: 8px;">
            <label style="display:block; margin-bottom: 10px;">
              Longueur : <strong>{{ generatorLength }}</strong>
              <input type="range" min="8" max="64" v-model="generatorLength" @input="generatePassword"
                style="width: 100%;" />
            </label>

            <div
              style="background: #f4f4f4; padding: 10px; border-radius: 4px; font-family: monospace; word-break: break-all; margin-bottom: 10px;">
              {{ generatedPassword }}
            </div>

            <p style="margin: 0 0 10px 0; font-size: 0.9em;">
              Force du mot de passe :
              <strong
                :style="{ color: passwordStrength === 'Fort' ? 'green' : passwordStrength === 'Moyen' ? 'orange' : 'red' }">
                {{ passwordStrength }}
              </strong>
            </p>

            <div style="display: flex; gap: 10px;">
              <button type="button" @click="generatePassword">Regénérer</button>
              <button type="button" @click="useGeneratedPassword">Utiliser ce mot de passe</button>
            </div>
          </div>

          <label>Catégorie
            <select name="password-form-category" required>
              <option value="">Sélectionnez une catégorie</option>
              <option
                v-for="category in categories.filter(c => c.id_categorie !== 'tout' && c.id_categorie !== 'favoris')"
                :key="category.id_categorie" :value="category.nom">
                {{ category.nom }}
              </option>
            </select>
          </label>
          <button class="sidebar-add-category" type="button" @click="openAddCategory">Ajouter une catégorie</button>

          <label class="favorite-option"><input type="checkbox" name="password-form-favorite" /> Ajouter aux
            favoris</label>

          <footer class="modal-actions">
            <button class="modal-cancel" type="button" @click="closeAddPassword">Annuler</button>
            <p v-if="addPasswordError" class="password-feedback error">{{ addPasswordError }}</p>
            <button type="submit" :disabled="addPasswordLoading">{{ addPasswordLoading ? "Enregistrement..." :
              "Enregistrer" }}</button>
          </footer>
        </form>
      </section>
      <div v-if="showAddCategory" class="modal-backdrop" @click.self="closeAddCategory">
        <section class="password-modal" role="dialog" aria-modal="true" aria-labelledby="add-category-title">
          <header class="modal-header">
            <div>
              <p class="eyebrow">Nouvelle catégorie</p>
              <h2 id="add-category-title">Ajouter une catégorie</h2>
            </div>

            <button class="modal-close" type="button" aria-label="Fermer" @click="closeAddCategory">
              &times;
            </button>
          </header>

          <form class="password-form" autocomplete="off" @submit.prevent="createCategory">
            <label>
              Nom de la catégorie

              <input v-model="newCategoryName" type="text" placeholder="Ex. Réseaux sociaux" maxlength="50" required />
            </label>

            <label>
              Description

              <textarea v-model="newCategoryDescription" placeholder="Ex. Vos comptes de réseaux sociaux."
                maxlength="255" rows="4" required></textarea>
            </label>

            <p v-if="addCategoryError" class="password-feedback error">
              {{ addCategoryError }}
            </p>

            <footer class="modal-actions">
              <button class="modal-cancel" type="button" @click="closeAddCategory">
                Annuler
              </button>

              <button type="submit" :disabled="addCategoryLoading">
                {{ addCategoryLoading ? "Création..." : "Créer la catégorie" }}
              </button>
            </footer>
          </form>
        </section>
      </div>
    </div>
  </div>
</template>