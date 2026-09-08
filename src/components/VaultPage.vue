<script setup>
import { computed, ref } from "vue";

defineProps({
  user: {
    type: Object,
    required: true
  }
});

const emit = defineEmits(["logout"]);
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

      <section class="vault-empty-state" aria-live="polite">
        <p class="eyebrow">{{ selectedCategory.label }}</p>
        <h2>{{ activeCategory === "all" ? "Votre coffre est prêt" : `Aucun élément dans ${selectedCategory.label}` }}</h2>
        <p>Les identifiants de cette catégorie apparaîtront ici.</p>
        <button type="button">Ajouter un identifiant</button>
      </section>
    </main>
  </div>
</template>