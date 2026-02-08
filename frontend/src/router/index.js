import { createRouter, createWebHistory } from 'vue-router'
import UserLogin from '../components/UserLogin.vue'
import Base from '../components/Base.vue'
import StudentDashboard from '../components/student/Dashboard.vue'
import CompanyDashboard from '../components/company/Dashboard.vue'
import AdminDashboard from '../components/admin/Dashboard.vue'
import Register from '../components/Register.vue'
import Home from '../components/Home.vue'

const routes = [
    {
        path: '/',
        name: 'Home',
        component: Home
    },
    {
        path: '/login',
        name: 'Login',
        component: UserLogin
    },
    {
        path: '/base',
        name: 'Base',
        component: Base,
        children: [
            {
                path: 'student/Dashboard',
                name: 'StudentDashboard',
                component: StudentDashboard
            },
            {
                path: 'company/Dashboard',
                name: 'CompanyDashboard',
                component: CompanyDashboard
            },
            {
                path: 'admin/Dashboard',
                name: 'AdminDashboard',
                component: AdminDashboard
            }
        ]
    },
    {
        path: '/register',
        name: 'Register',
        component: Register
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

export default router
