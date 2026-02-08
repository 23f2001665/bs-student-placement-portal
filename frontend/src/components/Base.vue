<template>
  <div class="container-fluid">
    <!-- Top bar -->
    <nav class="navbar navbar-light bg-light px-4">
      <span class="navbar-brand fw-bold">Placement Portal</span>

      <button class="btn btn-outline-danger btn-sm" @click="logout">
        Logout
      </button>
    </nav>

    <!-- Child dashboard renders here -->
    <div class="container mt-4">
      <router-view />
    </div>
  </div>
</template>

<script>

export default {
  name: "DashboardBase",

  mounted() {
    if (!localStorage.getItem("access_token")) {
      this.$router.replace("/login");
      alert("Please login to continue");
      return;
    }
    if (!localStorage.getItem("user_type")) {
      this.$router.replace("/login");
      alert("Invalid session. Please login again.");
      localStorage.removeItem("access_token");
      return;
    }
    if (!localStorage.getItem("is_active") || localStorage.getItem("is_active") === "false") {
      this.$router.replace("/");
      alert("Your account is inactive. Please contact support.");
      localStorage.removeItem("access_token");
      localStorage.removeItem("user_type");
      localStorage.removeItem("is_active");
      return;
    }
    

    console.log("Base mounted");
    const role = localStorage.getItem("user_type");

    if (!role) {
      this.$router.replace("/login");
      return;
    }

    // Redirect ONLY if user is at /dashboard
    if (this.$route.path === "/base") {
      this.$router.replace(`base/${role}/dashboard`);
    }
  },

  methods: {
    logout() {
      localStorage.removeItem("access_token");
      this.$router.push("/login");
    },
  },
};
</script>
