<script setup>
import { computed, ref } from "vue";
import { getPasswords } from "../../passwordsService.js";

const props = defineProps({
  user: {
    type: Object,
    required: true
  }
});

const emit = defineEmits(["logout"]);
const passwords = ref([]);
const passwordsLoading = ref(true);
const passwordsError = ref("");
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

async function fetchPasswords() {
  passwordsLoading.value = true;
  passwordsError.value = "";
  try {
    const data = await getPasswords(props.user.id);
    passwords.value = Array.isArray(data) ? data : [];
  } catch (error) {
    passwordsError.value = error.message || "Impossible de charger les mots de passe.";
    console.error("Erreur lors de la récupération des mots de passe:", error);
  } finally {
    passwordsLoading.value = false;
  }
}

fetchPasswords();
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
          <button type="button">Ajouter un identifiant</button>
        </div>

        <p v-if="passwordsLoading" class="password-feedback">Chargement des mots de passe...</p>
        <p v-else-if="passwordsError" class="password-feedback error">{{ passwordsError }}</p>
        <p v-else-if="passwords.length === 0" class="password-feedback">Aucun mot de passe enregistré.</p>
        <div v-else class="password-list">
          <article v-for="password in passwords" :key="password.id" class="password-card">
            <div class="password-service-icon">{{ (password.service || password.name || "?").charAt(0).toUpperCase() }}</div>
            <div class="password-card-details">
              <strong>{{ password.service || password.name }}</strong>
              <span>{{ password.login_ou_email || password.login || "Identifiant non renseigné" }}</span>
            </div>
            <code>{{ password.mdp || password.value }}</code>
          </article>
        </div>
      </section>

      <section v-else class="vault-empty-state" aria-live="polite">
        <p class="eyebrow">{{ selectedCategory.label }}</p>
        <h2>Aucun élément dans {{ selectedCategory.label }}</h2>
        <p>Les identifiants de cette catégorie apparaîtront ici.</p>
        <button type="button">Ajouter un identifiant</button>
      </section>
    </main>
  </div>
</template>