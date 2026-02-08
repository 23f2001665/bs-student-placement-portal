<template>
  <div id="main">
    <div class="container-fluid mt-4">
      <!-- Heading -->
      <div class="row mb-4">
        <div class="col text-center">
          <h2>User Registration</h2>
          <p class="text-muted">Create a new student or company account</p>
        </div>
      </div>

      <!-- Main Layout -->
      <div class="row">
        <!-- LEFT: User Type -->
        <div class="col-md-2">
          <div class="border rounded p-3">
            <h6 class="mb-3">User Type</h6>

            <div class="form-check mb-2">
              <input
                class="form-check-input"
                type="radio"
                value="student"
                v-model="form.role"
                id="roleStudent"
              />
              <label class="form-check-label" for="roleStudent">
                Student
              </label>
            </div>

            <div class="form-check">
              <input
                class="form-check-input"
                type="radio"
                value="company"
                v-model="form.role"
                id="roleCompany"
              />
              <label class="form-check-label" for="roleCompany">
                Company
              </label>
            </div>
          </div>
        </div>

        <!-- MIDDLE: Basic Details -->
        <div class="col-md-5">
          <div class="border rounded p-4">
            <h5 class="mb-3">Basic Details</h5>

            <div class="mb-3">
              <label class="form-label">Full Name</label>
              <input v-model="form.name" class="form-control" required />
            </div>

            <div class="mb-3">
              <label class="form-label">Email</label>
              <input
                v-model="form.email"
                type="email"
                class="form-control"
                required
                autocomplete="false"
              />
            </div>

            <div class="mb-3">
              <label class="form-label">Password</label>

              <div class="input-group">
                <input
                  :type="show_password ? 'text' : 'password'"
                  v-model="form.password"
                  class="form-control"
                  autocomplete="new-password"
                  required
                />

                <button
                  type="button"
                  class="btn btn-outline-secondary"
                  @click="show_password = !show_password"
                  tabindex="-1"
                >
                  <i
                    :class="show_password ? 'bi bi-eye-slash' : 'bi bi-eye'"
                  ></i>
                </button>
              </div>
            </div>

            <div class="mb-3">
              <label class="form-label">Confirm Password</label>

              <div class="input-group">
                <input
                  :type="show_confirm_password ? 'text' : 'password'"
                  v-model="form.confirm_password"
                  class="form-control"
                  autocomplete="new-password"
                  required
                />

                <button
                  type="button"
                  class="btn btn-outline-secondary"
                  @click="show_confirm_password = !show_confirm_password"
                  tabindex="-1"
                >
                  <i
                    :class="
                      show_confirm_password ? 'bi bi-eye-slash' : 'bi bi-eye'
                    "
                  ></i>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- RIGHT: Role-specific -->
        <div class="col-md-5">
          <div class="border rounded p-4">
            <h5 class="mb-3">
              {{
                form.role === "student"
                  ? "Student Details"
                  : form.role === "company"
                  ? "Company Details"
                  : "Select User Type"
              }}
            </h5>

            <!-- Student -->
            <div v-if="form.role === 'student'">
              <div class="mb-3">
                <label class="form-label">Roll Number</label>
                <input v-model="form.roll_number" class="form-control" />
              </div>

              <div class="mb-3">
                <label class="form-label">Date of Birth</label>
                <flat-pickr
                  v-model="form.dob"
                  :config="form.dob_config"
                  class="form-control"
                />
              </div>

              <div class="mb-3">
                <label class="form-label">Gender</label>
                <select class="form-select" v-model="form.gender">
                  <option disabled value="">Select Gender</option>
                  <option value="m">Male</option>
                  <option value="f">Female</option>
                  <option value="o">Other</option>
                </select>
              </div>

              <div class="mb-3">
                <label class="form-label">Admission Year</label>
                <input
                  type="number"
                  v-model.number="form.admission_year"
                  class="form-control"
                />
              </div>

              <div class="mb-3">
                <label class="form-label">Programme</label>
                <select v-model.number="form.programme_id" class="form-select">
                  <option disabled value="">Select Programme</option>
                  <option v-for="p in programmes" :key="p.id" :value="p.id">
                    {{ p.name }}
                  </option>
                </select>
              </div>

              <div class="mb-3">
                <label class="form-label">Branch</label>
                <select
                  v-model.number="form.branch_id"
                  class="form-select"
                  :disabled="!branches.length"
                >
                  <option disabled value="">Select Branch</option>
                  <option v-for="b in branches" :key="b.id" :value="b.id">
                    {{ b.name }}
                  </option>
                </select>
              </div>

              <div class="md-3">
                <label class="form-label">Current Level</label>
                <input
                  class="form-control"
                  type="number"
                  v-model.number="form.current_level"
                  :max="max_current_level"
                  min="1"
                />
              </div>

              <div class="mb-3">
                <label class="form-label">Current CGPA</label>
                <input
                  class="form-control"
                  type="number"
                  step="0.01"
                  min="0"
                  max="10"
                  v-model.number="form.cgpa"
                />
              </div>
            </div>

            <!-- Company -->
            <div v-if="form.role === 'company'">
              <div class="mb-3">
                <label class="form-label">Industry</label>
                <input
                  v-model="form.industry"
                  class="form-control"
                  :disabled="form.role !== 'company'"
                />
              </div>

              <div class="mb-3">
                <label class="form-label">Location</label>
                <input v-model="form.location" class="form-control" />
              </div>

              <div class="mb-3">
                <label class="form-label">Contact Number</label>
                <input v-model="form.contact_number" class="form-control" />
              </div>

              <div class="mb-3">
                <label class="form-label">Website</label>
                <input v-model="form.website" type="url" class="form-control" />
              </div>

              <div class="mb-3">
                <label class="form-l">Company's Description </label>
                <textarea
                  v-model="form.description"
                  class="form-control"
                  placeholder="Enter a brief description about the company."
                >
                </textarea>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Submit -->
      <div class="row mt-4">
        <div class="col text-center">
          <button class="btn btn-primary px-5" @click="submit">Register</button>
        </div>
      </div>
    </div>

    <div v-if="error" class="alert alert-danger py-2">
              {{ error }}
            </div>
  </div>
</template>


<script>
import FlatPickr from "vue-flatpickr-component";
import "flatpickr/dist/flatpickr.css";

export default {
  name: "Register",
  components: { FlatPickr },

  data() {
    return {
      dob: null,

      programmes: [], // full data from backend
      branches: [], // filtered branches
      show_password: false,
      show_confirm_password: false,

      form: {
        email: "",
        password: "",
        confirm_password: "",
        name: "",
        role: "",

        dob: "",
        dob_config: {
          dateFormat: "Y-m-d",
          minDate: "1950-01-01",
          maxDate: "2006-12-31",
          disableMobile: true,
        },
        gender: "",
        roll_number: "",
        admission_year: null,
        current_level: null,
        max_current_level: null,
        programme_id: null,
        branch_id: null,
        cgpa: null,

        industry: "",
        location: "",
        website: "",
        description: "",
        contact_number: "",
      },
    };
  },

  mounted() {
    this.loadProgrammes();
  },

  watch: {
    "form.programme_id"(newVal) {
      this.updateBranches(newVal);
    },
  },

  computed: {
    max_current_level() {
      if (!this.programmes.length || !this.form.programme_id) {
        return 10;
      }

      const prog = this.programmes.find(
        (p) => p.id === Number(this.form.programme_id)
      );

      return prog?.duration_years ?? 10;
    },
  },

  methods: {
    async loadProgrammes() {
      const cached = localStorage.getItem("programmes");

      if (cached) {
        this.programmes = JSON.parse(cached);
        return;
      }

      try {
        const res = await fetch(
          "http://127.0.0.1:5000/public/programmes_and_branches"
        );
        const data = await res.json();

        this.programmes = data;
        localStorage.setItem("programmes", JSON.stringify(data));
      } catch (err) {
        console.error("Failed to load programmes", err);
      }
    },

    updateBranches(programmeId) {
      this.branches = [];
      this.form.branch_id = null;

      if (!programmeId) return;

      const selected = this.programmes.find((p) => p.id === programmeId);

      this.branches = selected ? selected.branches : [];
    },

    validateForm() {
      this.errors = {};
      this.serverError = null;

      // email
      if (!this.form.email) {
        this.errors.email = "Email is required";
      } else if (!/^\S+@\S+\.\S+$/.test(this.form.email)) {
        this.errors.email = "Invalid email format";
      }

      // password
      if (!this.form.password || this.form.password.length < 8) {
        this.errors.password = "Password must be at least 8 characters";
      }

      if (this.form.password !== this.form.confirm_password) {
        this.errors.confirm_password = "Passwords do not match";
      }

      // name
      if (!/^[a-zA-Z ]{3,63}$/.test(this.form.name)) {
        this.errors.name = "Name must be 3–63 letters only";
      }

      // role-specific
      if (this.form.role === "student") {
        if (!this.form.dob) this.errors.dob = "Date of birth required";

        if (!/^[A-Za-z0-9]{10}$/.test(this.form.roll_number)) {
          this.errors.roll_number = "Roll number must be 10alphanumerics";
        }

        if (
          this.form.admission_year < 2000 ||
          this.form.admission_year > 2100
        ) {
          this.errors.admission_year = "Invalid admission year";
        }

        if (
          this.form.current_level < 1 ||
          this.form.current_level > this.max_current_level
        ) {
          this.errors.current_level = "Level must be between 1 and 10";
        }
      }

      if (this.form.role === "company") {
        if (this.form.description?.length < 10) {
          this.errors.description = "Description too short";
        }
      }
      console.log(this.errors);
      return Object.keys(this.errors).length === 0;
    },

    async submit() {
      if (!this.validateForm()) return;

      this.loading = true;
      this.serverError = null;

      const payload = { ...this.form };
      payload.roll_number = payload.roll_number.toUpperCase();
      delete payload.dob_config;
      delete payload.confirm_password;
      delete payload.max_current_level;

      const removeFields = (obj, fields) => {
        fields.forEach((f) => delete obj[f]);
      };

      if (payload.role === "student") {
        removeFields(payload, [
          "location",
          "website",
          "contact_number",
          "description",
          "industry",
        ]);
      } else if (payload.role === "company") {
        removeFields(payload, [
          "admission_year",
          "branch_id",
          "programme_id",
          "roll_number",
          "current_level",
          "cgpa",
          "dob",
          "gender",
        ]);
      }

      try {
        const res = await fetch(
          this.form.role === "student"
            ? "http://localhost:5000/auth/register/student"
            : "http://localhost:5000/auth/register/company",
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          }
        );

        const data = await res.json();

        if (!res.ok) {
          // backend errors
          if (res.status === 409) {
            this.serverError = data.error;
          } else if (data.errors) {
            // marshmallow validation errors
            this.errors = data.errors;
          } else {
            this.serverError = "Registration failed";
          }
          return;
        }

        // success
        alert("Registration successful! Redirecting to login...");
        this.$router.push("/login");
      } catch (err) {
        this.serverError = "Network error. Please try again.";
      } finally {
        this.loading = false;
      }
    },
  },
};
</script>

<style scoped>
/* Page heading */
h2 {
  color: #0d6efd;
  font-size: 3rem;
  font-weight: 600;
  font-family: Georgia, "Times New Roman", Times, serif;
  letter-spacing: 0.5px;
}

/* User type panel */
.col-md-2 .border {
  background: #fea2a2;
}

/* Form labels */
.form-label {
  font-size: 0.9rem;
  font-weight: 500;
  color: #495057;
}

/* Right panel dynamic title */
.col-md-5 h5 {
  color: #031220;
}

/* Submit button */
button.btn-primary {
  padding: 0.6rem 2.5rem;
  font-weight: 500;
  letter-spacing: 0.4px;
}

#main {
  margin: auto;
  /* scale: 0.9; */
  background: linear-gradient(180deg, #f8f9fa, #ffffff);
  min-height: 100vh;
}

/* Eye icon */
.bi {
  color: #000;
  font-size: 1.1rem;
}

/* Remove button chrome */
.input-group .btn {
  border: none;
  background: transparent;
}

.input-group .btn:hover {
  background: #f8f9fa;
}

</style>