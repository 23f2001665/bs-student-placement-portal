<template>
  <h3 class="fw-bold">Admin Dashboard</h3>
  <p class="text-muted">System overview and controls</p>
</template>

<script>
export default {
  name: "AdminDashboard",

  mounted() {
    if (localStorage.getItem("user_type") !== "admin") {
      this.$router.replace("/login");
      return;
    }
    console.log("Admin dashboard mounted");
  },
};
</script>
