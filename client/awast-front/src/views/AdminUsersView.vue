<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useUserStore } from '@/stores/userStore';
import { storeToRefs } from 'pinia';
import type { UserCreate, UserUpdate } from '@/types/api';

const userStore = useUserStore();
const { users, isLoading } = storeToRefs(userStore);

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
  user_id: '',
  username: '',
  email: '',
  password: '',
  role: 'user',
  enabled_domains: [] as string[],
});
const defaultItem = {
  user_id: '',
  username: '',
  email: '',
  password: '',
  role: 'user',
  enabled_domains: [] as string[],
};

const formTitle = computed(() => {
  return editedIndex.value === -1 ? 'New User' : 'Edit User';
});

const errorMsg = ref('');

onMounted(async () => {
  await userStore.fetchUsers();
});

const close = () => {
  dialog.value = false;
  errorMsg.value = '';
  setTimeout(() => {
    editedItem.value = { ...defaultItem, enabled_domains: [] };
    editedIndex.value = -1;
  }, 300);
};

const closeDelete = () => {
  dialogDelete.value = false;
  setTimeout(() => {
    editedItem.value = { ...defaultItem, enabled_domains: [] };
    editedIndex.value = -1;
  }, 300);
};

const save = async () => {
  errorMsg.value = '';
  try {
    if (editedIndex.value > -1) {
      const updateData: UserUpdate = {
        username: editedItem.value.username,
        email: editedItem.value.email,
        role: editedItem.value.role,
        enabled_domains: editedItem.value.enabled_domains,
      };
      if (editedItem.value.password) {
        updateData.password = editedItem.value.password;
      }
      await userStore.updateUser(editedItem.value.user_id, updateData);
    } else {
      const createData: UserCreate = {
        username: editedItem.value.username,
        email: editedItem.value.email,
        password: editedItem.value.password,
        role: editedItem.value.role,
        enabled_domains: editedItem.value.enabled_domains,
      };
      await userStore.createUser(createData);
    }
    close();
  } catch (error: any) {
    errorMsg.value = error?.response?.data?.detail || 'Operation failed';
  }
};

const editItem = (item: any) => {
  editedIndex.value = users.value.findIndex(u => u.user_id === item.user_id);
  editedItem.value = { ...item, password: '' };
  dialog.value = true;
};

const deleteItem = (item: any) => {
  editedIndex.value = users.value.findIndex(u => u.user_id === item.user_id);
  editedItem.value = { ...item };
  dialogDelete.value = true;
};

const deleteItemConfirm = async () => {
  try {
    await userStore.deleteUser(editedItem.value.user_id);
    closeDelete();
  } catch (error: any) {
    errorMsg.value = error?.response?.data?.detail || 'Delete failed';
  }
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
          :loading="isLoading"
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
            <v-alert v-if="errorMsg" type="error" variant="tonal" density="compact" class="mb-4">{{ errorMsg }}</v-alert>
            <v-container>
              <v-row>
                <v-col cols="12">
                  <v-text-field v-model="editedItem.username" label="Username" variant="outlined"></v-text-field>
                </v-col>
                <v-col cols="12">
                  <v-text-field v-model="editedItem.email" label="Email" variant="outlined"></v-text-field>
                </v-col>
                <v-col cols="12">
                  <v-text-field
                    v-model="editedItem.password"
                    :label="editedIndex === -1 ? 'Password' : 'New Password (leave blank to keep)'"
                    type="password"
                    variant="outlined"
                  ></v-text-field>
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
            <v-btn color="blue-darken-1" variant="text" @click="save" :loading="isLoading">Save</v-btn>
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
            <v-btn color="error" variant="elevated" @click="deleteItemConfirm" :loading="isLoading">Delete</v-btn>
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
