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

          <!-- Success -->
          <div v-if="submitted" class="alert alert-success mt-3">
            Login successful
          </div>
        </div>
      </div>
    </div>
  </div>
</template>


<script>
export default {
  name: "Login",

  data() {
    return {
      showPassword: false,
      submitted: false,
      loading: false,
      error: null,
      body: {
        email: "",
        password: "",
      },
    };
  },

  methods: {

    async me(){
      try {
        const res = await fetch("http://localhost:5000/auth/me", {
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${localStorage.getItem("access_token")}`,
          },
        });
        const data = await res.json();
        // console.log(data);
        localStorage.setItem("user_type", data.role);
        localStorage.setItem("is_active", data.is_active);
      } catch (err) {
        console.error("Failed to fetch user data", err);
      }
    },

    async submitForm() {
      this.error = null;
      this.submitted = false;

      if (localStorage.getItem("access_token")) {
        this.error = "Already logged in";
        return;
      }

      this.loading = true;
      const payload = {
        email: this.body.email.trim(),
        password: this.body.password,
      };

      try {
        const res = await fetch("http://localhost:5000/auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });

        const data = await res.json();

        if (!res.ok) {
          this.error = data.error || "Invalid credentials";
          return;
        }

        localStorage.setItem("access_token", data.access_token);
        this.submitted = true;

        await this.me();
        this.$router.push("/base");
      } catch (err) {
        this.error = "Network error. Please try again.";
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
