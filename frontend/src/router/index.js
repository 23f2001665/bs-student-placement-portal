import { createRouter, createWebHistory } from "vue-router";

import Home from "../components/Home.vue";
import UserLogin from "../components/UserLogin.vue";
import ForgotPassword from "../components/ForgotPassword.vue";
import Register from "../components/Register.vue";

import Base from "../components/Base.vue";

import StudentDashboard from "../components/student/Dashboard.vue";
import CompanyDashboard from "../components/company/Dashboard.vue";

import AdminDashboard from "../components/admin/AdminDashboard.vue";
import AdminStudents from "../components/admin/AdminStudents.vue";
import Programmes from "../components/admin/AdminProgrammes.vue";

const routes = [
  {
    path: "/",
    name: "Home",
    component: Home,
  },

  {
    path: "/login",
    name: "Login",
    component: UserLogin,
  },

  {
    path: "/forgot-password",
    name: "ForgotPassword",
    component: ForgotPassword,
  },

  {
    path: "/register",
    name: "Register",
    component: Register,
  },

  {
    path: "/base",
    component: Base,
    meta: { requiresAuth: true },

    children: [
      {
        path: "student",
        name: "StudentDashboard",
        component: StudentDashboard,
        meta: { role: "student" },
      },

      {
        path: "company",
        name: "CompanyDashboard",
        component: CompanyDashboard,
        meta: { role: "company" },
      },

      {
        path: "admin",
        component: AdminDashboard,
        meta: { role: "admin" },

        children: [
          {
            path: "students",
            name: "AdminStudents",
            component: AdminStudents,
            meta: { role: "admin" },
          },

          {
            path: "programmes",
            name: "AdminProgrammes",
            component: Programmes,
            meta: { role: "admin" },
          },
        ],
      },
    ],
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;

router.beforeEach((to, from, next) => {

  const token = localStorage.getItem("access_token");
  const role = localStorage.getItem("user_role");
  const isActive = localStorage.getItem("is_active");

  const isLoggedIn = !!token;

  /* Public pages */
  const publicPages = ["/", "/login", "/register"];

  if (publicPages.includes(to.path)) {

    // Prevent logged-in user from going back to login
    if (isLoggedIn && (to.path === "/login" || to.path === "/register")) {
      return next(`/base/${role}`);
    }

    return next();
  }

  /* Protected routes */
  if (to.meta.requiresAuth) {

    if (!isLoggedIn || !role) {
      localStorage.clear();
      return next("/login");
    }

    if (isActive === "false") {
      localStorage.clear();
      return next("/");
    }
  }

  /* Role-based protection */
  if (to.meta.role) {

    if (role !== to.meta.role) {
      return next(`/base/${role}`);
    }
  }

  next();
});
