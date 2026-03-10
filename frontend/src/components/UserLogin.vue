<template>
  <div
    class="container vh-100 d-flex align-items-center justify-content-center"
  >
    <div class="col-md-4">
      <div class="card shadow-sm">
        <div class="card-body">
          <h4 class="text-center mb-4">Login</h4>

          <form @submit.prevent="submitForm" autocomplete="off">
            <!-- Email -->
            <div class="mb-3">
              <label class="form-label">Email</label>
              <input
                type="email"
                v-model="body.email"
                class="form-control"
                autocomplete="new-email"
                required
              />
            </div>

            <!-- Password -->
            <!-- Password -->
            <div class="mb-3">
              <label class="form-label">Password</label>

              <div class="input-group">
                <input
                  :type="showPassword ? 'text' : 'password'"
                  v-model="body.password"
                  class="form-control"
                  autocomplete="new-password"
                  required
                />

                <button
                  type="button"
                  class="btn btn-outline-secondary"
                  id="togglePassword"
                  @click="showPassword = !showPassword"
                  tabindex="-1"
                >
                  <i
                    :class="showPassword ? 'bi bi-eye-slash' : 'bi bi-eye'"
                  ></i>
                </button>
              </div>
            </div>

            <!-- Error -->
            <div v-if="error" class="alert alert-danger py-2">
              {{ error }}
            </div>

            <!-- Submit -->
            <div class="d-grid mt-3">
              <button class="btn btn-primary" type="submit" :disabled="loading">
                {{ loading ? "Logging in..." : "Login" }}
              </button>
            </div>
          </form>

          <p class="text-center mt-3">
            Don't have an account?
            <router-link to="Register">Register here</router-link>
          </p>

          <p class="text-center mt-3"> forgot password? <router-link :to="{name: 'ForgotPassword'}">Reset here</router-link> </p>
        </div>
      </div>
    </div>
  </div>
</template>


<script>
import sleep from "@/utils/sleep";
import api from "@/services/api";
import { toast } from "vue3-toastify";

export default {
  name: "Login",

  data() {
    return {
      showPassword: false,
      loading: false,
      error: null,
      body: {
        email: "",
        password: "",
      },
    };
  },

  methods: {
    async me() {
      const res = await api.get("/auth/me");

      const data = res.data;

      localStorage.setItem("user_role", data.role);
      localStorage.setItem("is_active", data.is_active);
    },

    async submitForm() {
      if (this.loading) return;

      this.loading = true;
      this.error = null;

      try {
        const res = await api.post("/auth/login", {
          email: this.body.email.trim(),
          password: this.body.password,
        });

        localStorage.setItem("access_token", res.data.access_token);

        await this.me();

        toast.success("Login successful");
        sleep(1000);

        this.$router.push(`/base/${localStorage.getItem("user_role")}`);

      } catch (err) {

        this.error =
          err.response?.data?.error || "Invalid credentials";

      } finally {
        this.loading = false;
      }
    },
  },
};
</script>

<style scoped>
/* Keep inputs stable */
input:focus {
  box-shadow: 0 0 0 0.15rem rgba(13, 110, 253, 0.25);
}

/* Optional subtle hover */
button:hover {
  transform: translateY(-1px);
}

.bi {
  color: black;
  font-size: 1.2rem;
  background: transparent;
}

#togglePassword {
  border: none;
  background: transparent;
  padding: 0.25rem 0.5rem;
  cursor: pointer;
}
</style>
