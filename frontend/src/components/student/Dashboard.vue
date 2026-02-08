<template>
  <h3 class="fw-bold">Student Dashboard</h3>
  <p class="text-muted">Welcome, student 👋</p>
</template>

<script>
export default {
  name: "StudentDashboard",

  mounted() {
    if (localStorage.getItem("user_type") !== "student") {
      this.$router.replace("/login");
      return;
    }
    console.log("Student dashboard mounted");
  },
};
</script>
