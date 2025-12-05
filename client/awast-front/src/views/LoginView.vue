<script setup lang="ts">
import { ref } from 'vue'
import loginImage from '../assets/img/login-left-side.jpeg'
import logo from '../assets/img/logo.svg'
import { useRouter } from 'vue-router'

const visible = ref(false)
const router = useRouter()

function signIn(){
 router.push('/dashboard')
}

</script>

<template>
  <v-container fluid class="pa-0">
    <v-row>
      <v-col cols="12" md="8" class="left-side pb-0 pr-0">
        <v-img
            :src=loginImage
            alt="Login Image"
            cover
            min-height="100vh"
        ></v-img>
      </v-col>
      <v-col cols="12" md="4" class="right-side d-flex align-center justify-center pl-0">
        <v-card width="400" elevation="0">
          <v-card-title class="text-h5 text-center">
            <div class="d-flex justify-center">
              <v-img
                  :src=logo
                  alt="Login Image"
                  max-width="200"
                  class="logo"
              >
              </v-img>
            </div>
            Nice to see you again
          </v-card-title>
          <v-card-text>
            <v-form>
              <v-label>Email</v-label>
              <v-text-field
                  density="compact"
                  placeholder="Email address"
                  prepend-inner-icon="mdi-email-outline"
                  variant="outlined"
              ></v-text-field>
              <v-label>Password</v-label>
              <v-text-field
                  :append-inner-icon="visible ? 'mdi-eye-off' : 'mdi-eye'"
                  :type="visible ? 'text' : 'password'"
                  density="compact"
                  placeholder="Enter your password"
                  prepend-inner-icon="mdi-lock-outline"
                  variant="outlined"
                  @click:append-inner="visible = !visible"
              ></v-text-field>
              <v-btn
                  height="40"
                  color="var(--button-bg)"
                  rounded="lg"
                  size="x-large"
                  class="btn-text"
                  block
                  elevation="0"
                  @click="signIn"
              >Sign In</v-btn>
            </v-form>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<style scoped>
.btn-text{
  color: var(--btn-text);
  text-transform: capitalize;
}
</style>