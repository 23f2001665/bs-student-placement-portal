// import { create } from 'node:domain';

console.log('Hello World');

result = fetch('http://localhost:5000/api/ping')
console.log(result);
// result = result.then(res => res.json());
// console.log(result);

// const app = Vue.createApp({
//     data() {
//         return {
//             user: {
//                 greet: 'Hi there!',
//                 name: 'User',
//                 count: 0
//             }
//         };
//     },
//     methods: {
//         increment() {
//             this.user.count++;
//         }
//     },
// });

// const vm = app.mount('#app');


// console.log(vm.user.greet);

