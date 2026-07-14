import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import DataTable from 'datatables.net-vue3'
import DataTablesCore from 'datatables.net-bs5'

import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap/dist/js/bootstrap.bundle.min.js'
import 'datatables.net-bs5/css/dataTables.bootstrap5.min.css'

DataTable.use(DataTablesCore)

createApp(App).use(router).component('DataTable', DataTable).mount('#app')
