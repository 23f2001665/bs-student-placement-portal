<template>
  <h3 class="fw-bold">Company Dashboard</h3>
  <p class="text-muted">Manage job postings and applications</p>
</template>

<script>
export default {
  name: "CompanyDashboard",

  mounted() {
    if (localStorage.getItem("user_type") !== "company") {
      this.$router.replace("/login");
      return;
    }
    console.log("Company dashboard mounted");
  },
};
</script>
