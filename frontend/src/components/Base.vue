<template>
  <div class="container-fluid">

    <nav class="navbar navbar-light bg-light px-4">
      <span class="navbar-brand fw-bold">Placement Portal</span>

      <button class="btn btn-outline-danger btn-sm" @click="logout">
        Logout
      </button>
    </nav>

    <div class="container mt-4">
      <router-view />
    </div>

  </div>
</template>

<script>
export default {
  name: "DashboardBase",

  mounted() {
    // If user visits only /base → redirect to their role page
    if (this.$route.path === "/base") {
      const role = localStorage.getItem("user_type");
      this.$router.replace(`/base/${role}`);
    }
  },

  methods: {
    logout() {
      const token = localStorage.getItem("access_token");

      localStorage.clear();

      fetch("http://localhost:5000/auth/logout", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }).finally(() => {
        this.$router.replace("/login");
      });
    },
  },
};
</script>

