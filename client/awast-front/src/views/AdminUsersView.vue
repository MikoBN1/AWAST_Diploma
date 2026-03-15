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
const newDomainInput = ref('');

onMounted(async () => {
  await userStore.fetchUsers();
});

const close = () => {
  dialog.value = false;
  errorMsg.value = '';
  setTimeout(() => {
    editedItem.value = { ...defaultItem, enabled_domains: [] };
    editedIndex.value = -1;
    newDomainInput.value = '';
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
        role: (editedItem.value.role || '').toLowerCase(),
        enabled_domains: editedItem.value.enabled_domains ?? [],
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
        role: (editedItem.value.role || '').toLowerCase(),
        enabled_domains: editedItem.value.enabled_domains ?? [],
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
  editedItem.value = { ...item, password: '', enabled_domains: Array.isArray(item?.enabled_domains) ? [...item.enabled_domains] : [] };
  dialog.value = true;
};

const addDomain = () => {
  const domain = newDomainInput.value?.trim();
  if (domain) {
    editedItem.value.enabled_domains = [...(editedItem.value.enabled_domains || []), domain];
    newDomainInput.value = '';
  }
};
const removeDomain = (index: number) => {
  const list = [...(editedItem.value.enabled_domains || [])];
  list.splice(index, 1);
  editedItem.value.enabled_domains = list;
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
      <v-dialog v-model="dialog" max-width="800px" persistent>
        <v-card class="rounded-xl overflow-hidden" elevation="12">
          <v-row no-gutters>
            <v-col cols="12" md="4" class="bg-blue-darken-3 pa-8 d-flex flex-column">
              <v-icon size="48" color="white" class="mb-6">mdi-account-cog-outline</v-icon>
              <h2 class="text-h4 font-weight-bold text-white mb-4">
                {{formTitle}}
              </h2>
              <p class="text-body-2 text-blue-lighten-4">
                Update credentials and domain permissions for the sentinel operator.
              </p>
              <v-spacer></v-spacer>
              <div style="width: 40px; height: 4px; background: rgba(255,255,255,0.3); border-radius: 2px;"></div>
            </v-col>

            <v-col cols="12" md="8" class="pa-10 bg-grey-lighten-5">
              <v-alert v-if="errorMsg" type="error" density="compact" class="mb-4" closable>{{ errorMsg }}</v-alert>
              <v-row>
                <v-col cols="12" sm="7">
                  <label class="text-overline font-weight-bold text-grey-darken-1">USERNAME</label>
                  <v-text-field
                    v-model="editedItem.username"
                    variant="outlined"
                    bg-color="grey-lighten-3"
                    class="mt-1 rounded-lg"
                    hide-details
                  ></v-text-field>
                </v-col>

                <v-col cols="12" sm="5">
                  <label class="text-overline font-weight-bold text-grey-darken-1">ROLE</label>
                  <v-select
                    v-model="editedItem.role"
                    :items="['admin', 'analyst', 'user']"
                    variant="outlined"
                    bg-color="grey-lighten-3"
                    class="mt-1 rounded-lg"
                    hide-details
                  ></v-select>
                </v-col>

                <v-col cols="12">
                  <label class="text-overline font-weight-bold text-grey-darken-1">EMAIL ADDRESS</label>
                  <v-text-field
                    v-model="editedItem.email"
                    variant="outlined"
                    bg-color="grey-lighten-3"
                    class="mt-1 rounded-lg"
                    hide-details
                  ></v-text-field>
                </v-col>

                <v-col cols="12">
                  <div class="d-flex justify-space-between align-center">
                    <label class="text-overline font-weight-bold text-grey-darken-1">NEW PASSWORD</label>
                    <v-chip size="x-small" color="orange-lighten-4" text-color="orange-darken-4" class="font-weight-black">
                      LEAVE BLANK TO KEEP
                    </v-chip>
                  </div>
                  <v-text-field
                    v-model="editedItem.password"
                    type="password"
                    variant="outlined"
                    bg-color="grey-lighten-3"
                    class="mt-1 rounded-lg"
                    hide-details
                  ></v-text-field>
                </v-col>

                <v-col cols="12">
                  <label class="text-overline font-weight-bold text-grey-darken-1">ENABLED DOMAINS</label>
                  <v-card variant="flat" class="bg-blue-lighten-5 pa-4 mt-1 rounded-lg">
                    <v-chip-group column>
                      <v-chip
                        v-for="(domain, i) in editedItem.enabled_domains"
                        :key="i"
                        closable
                        color="white"
                        class="text-grey-darken-3 shadow-sm"
                        @click:close="removeDomain(i)"
                      >
                        {{ domain }}
                      </v-chip>
                    </v-chip-group>
                    <div class="d-flex gap-2 mt-2 align-center">
                      <v-text-field
                        v-model="newDomainInput"
                        placeholder="e.g. example.com"
                        variant="outlined"
                        density="compact"
                        rounded="lg"
                        hide-details
                        class="flex-grow-1 mr-2"
                        bg-color="white"
                        @keyup.enter="addDomain"
                      ></v-text-field>
                      <v-btn
                        variant="outlined"
                        color="primary"
                        prepend-icon="mdi-plus"
                        class="bg-white"
                        rounded="lg"
                        @click="addDomain"
                      >
                        Add Domain
                      </v-btn>
                    </div>
                  </v-card>
                </v-col>
              </v-row>

              <div class="d-flex justify-end align-center mt-8">
                <v-btn variant="text" class="text-none font-weight-bold mr-4" @click="close">
                  Cancel
                </v-btn>
                <v-btn
                  color="blue-darken-2"
                  size="large"
                  class="px-8 rounded-lg text-none"
                  elevation="0"
                  @click="save"
                  :loading="isLoading"
                >
                  Save Changes
                </v-btn>
              </div>
            </v-col>
          </v-row>
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

/* Specific styling for the 'flat' input look in the photo */
:deep(.v-field__input) {
  min-height: 48px !important;
}
.text-overline {
  letter-spacing: 0.1em !important;
  font-size: 0.7rem !important;
}
</style>
