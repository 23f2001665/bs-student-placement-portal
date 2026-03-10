<template>
  <div
    class="container-fluid vh-100 d-flex align-items-center justify-content-center"
  >
    <div class="text-center p-5 border rounded shadow-sm bg-white">
      <h1 class="mb-4">Placement Portal</h1>

      <p class="text-muted mb-4">Login or register to continue</p>

      <div class="d-grid gap-3 col-6 mx-auto">
        <router-link to="/login" class="btn btn-outline-primary">
          Login
        </router-link>

        <router-link to="/register" class="btn btn-outline-primary">
          Register
        </router-link>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "Home",
  mounted() {
    const role = localStorage.getItem("user_role");

    if (role) {
      this.$router.push(`/base/${role}`);
    }
  },
};
</script>

<style scoped>
/* No custom colors — Bootstrap only */
h1 {
  font-weight: 600;
  font-family: "Times New Roman", Times, serif;
}

.bg-white {
  background-color: rgba(255, 255, 255, 0.95);
}
</style>
