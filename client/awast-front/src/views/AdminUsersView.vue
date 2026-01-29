<script setup lang="ts">
import { ref } from 'vue';

// Mock Data
const users = ref([
  { id: '1', username: 'admin', email: 'admin@awast.com', role: 'admin', enabled_domains: ['*'] },
  { id: '2', username: 'user1', email: 'user1@example.com', role: 'user', enabled_domains: ['example.com'] },
  { id: '3', username: 'auditor', email: 'auditor@company.com', role: 'user', enabled_domains: ['company.com', 'subsidiary.com'] },
]);

const dialog = ref(false);
const dialogDelete = ref(false);
const headers = [
  { title: 'Username', key: 'username' },
  { title: 'Email', key: 'email' },
  { title: 'Role', key: 'role' },
  { title: 'Domains', key: 'enabled_domains' },
  { title: 'Actions', key: 'actions', sortable: false },
];

const editedIndex = ref(-1);
const editedItem = ref({
  id: '',
  username: '',
  email: '',
  role: 'user',
  enabled_domains: [] as string[],
});
const defaultItem = {
  id: '',
  username: '',
  email: '',
  role: 'user',
  enabled_domains: [],
};

const formTitle = computed(() => {
  return editedIndex.value === -1 ? 'New User' : 'Edit User';
});

import { computed } from 'vue';

const close = () => {
  dialog.value = false;
  setTimeout(() => {
    editedItem.value = Object.assign({}, defaultItem);
    editedIndex.value = -1;
  }, 300);
};

const closeDelete = () => {
  dialogDelete.value = false;
  setTimeout(() => {
    editedItem.value = Object.assign({}, defaultItem);
    editedIndex.value = -1;
  }, 300);
};

const save = () => {
  if (editedIndex.value > -1 && users.value[editedIndex.value]) {
    Object.assign(users.value[editedIndex.value], editedItem.value);
  } else {
    // Mock ID generation
    users.value.push({ ...editedItem.value, id: String(users.value.length + 1) });
  }
  close();
};

const editItem = (item: any) => {
  editedIndex.value = users.value.indexOf(item);
  editedItem.value = JSON.parse(JSON.stringify(item)); // Deep copy mainly for arrays
  dialog.value = true;
};

const deleteItem = (item: any) => {
  editedIndex.value = users.value.indexOf(item);
  editedItem.value = Object.assign({}, item);
  dialogDelete.value = true;
};

const deleteItemConfirm = () => {
  users.value.splice(editedIndex.value, 1);
  closeDelete();
};
</script>

<template>
  <div class="admin-users-container">
    <v-container>
      <div class="d-flex justify-space-between align-center mb-6">
        <div>
           <div class="text-overline text-primary">Administration</div>
           <h1 class="text-h3 font-weight-bold text-slate-800">User Management</h1>
        </div>
        <v-btn color="primary" prepend-icon="mdi-plus" @click="dialog = true">Add User</v-btn>
      </div>

      <v-card class="glass-card" elevation="0">
        <v-data-table
          :headers="headers"
          :items="users"
          class="bg-transparent"
        >
          <template v-slot:item.role="{ item }">
            <v-chip :color="item.role === 'admin' ? 'purple' : 'blue'" size="small" class="text-uppercase font-weight-bold">
              {{ item.role }}
            </v-chip>
          </template>

          <template v-slot:item.enabled_domains="{ item }">
              <v-chip v-for="domain in item.enabled_domains" :key="domain" size="x-small" class="mr-1 mb-1">
                  {{ domain }}
              </v-chip>
          </template>

          <template v-slot:item.actions="{ item }">
            <v-icon size="small" class="mr-2" @click="editItem(item)" color="primary">mdi-pencil</v-icon>
            <v-icon size="small" @click="deleteItem(item)" color="error">mdi-delete</v-icon>
          </template>
        </v-data-table>
      </v-card>

      <!-- Edit/Create Dialog -->
      <v-dialog v-model="dialog" max-width="500px">
        <v-card class="rounded-lg pa-4">
          <v-card-title>
            <span class="text-h5">{{ formTitle }}</span>
          </v-card-title>

          <v-card-text>
            <v-container>
              <v-row>
                <v-col cols="12">
                  <v-text-field v-model="editedItem.username" label="Username" variant="outlined"></v-text-field>
                </v-col>
                <v-col cols="12">
                  <v-text-field v-model="editedItem.email" label="Email" variant="outlined"></v-text-field>
                </v-col>
                <v-col cols="12" sm="6">
                  <v-select v-model="editedItem.role" :items="['admin', 'user']" label="Role" variant="outlined"></v-select>
                </v-col>
                  <v-col cols="12">
                       <v-combobox
                          v-model="editedItem.enabled_domains"
                          chips
                          multiple
                          label="Enabled Domains"
                          placeholder="Type and press enter to add"
                          variant="outlined"
                        ></v-combobox>
                </v-col>
              </v-row>
            </v-container>
          </v-card-text>

          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn color="blue-darken-1" variant="text" @click="close">Cancel</v-btn>
            <v-btn color="blue-darken-1" variant="text" @click="save">Save</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>

      <!-- Delete Confirmation Dialog -->
      <v-dialog v-model="dialogDelete" max-width="500px">
        <v-card class="rounded-lg pa-4">
          <v-card-title class="text-h5 text-center">Are you sure?</v-card-title>
          <v-card-text class="text-center text-body-1">Disabling this user will prevent them from accessing the platform.</v-card-text>
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn color="blue-darken-1" variant="text" @click="closeDelete">Cancel</v-btn>
            <v-btn color="error" variant="elevated" @click="deleteItemConfirm">Delete</v-btn>
            <v-spacer></v-spacer>
          </v-card-actions>
        </v-card>
      </v-dialog>
    </v-container>
  </div>
</template>

<style scoped>
.admin-users-container {
    min-height: 100vh;
    background: #f1f5f9;
}

.glass-card {
  background: white !important;
  border-radius: 12px;
  border: 1px solid rgba(0,0,0,0.05);
}
</style>
