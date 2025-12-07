<script setup lang="ts">
interface Vulnerability{

}
</script>

<template>
<v-card width="80vw">
  <v-card-title>
    Vulnerabilities
    <p class="sub-text">Latest security issues detected in your codebase</p>
  </v-card-title>
  <v-card-text>
    <div class="vuln-container mb-4" v-for="i in 10" :key="i">
      <div class="mb-3">
        <v-chip label color="red" variant="flat">
          <span class="mdi mdi-alert mr-1"></span>
          High
        </v-chip>
        <span class="cve-info pl-4">#OWASP_2021_A05</span>
      </div>
      <div class="mb-3">
        <h4 class="mb-1">SQL Injection in User Authentication</h4>
        <p class="sub-text">Description: Unsanitized user input directly concatenated to SQL query</p>
        <br/>
        <p class="sub-text">Solution: Modern Web browsers support the Content-Security-Policy and X-Frame-Options HTTP headers. Ensure one of them is set on all web pages returned by your site/app.
          If you expect the page to be framed only by pages on your server (e.g. it's part of a FRAMESET) then you'll want to use SAMEORIGIN, otherwise if you never expect the page to be framed, you should use DENY. Alternatively consider implementing Content Security Policy's "frame-ancestors" directive.</p>
      </div>
      <div class="vuln-footer">
        Method: GET
      </div>
      <v-btn class="exploit-btn" variant="flat">
        Exploit
      </v-btn>
    </div>
  </v-card-text>
</v-card>
</template>

<style scoped>
.sub-text{
  font-size: 15px;
  color: var(--sub-text);
}
h4{
  font-size: 18px;
}
.vuln-footer{
  color: var(--sub-text);
  font-size: 12px;
}
.cve-info{
  color: var(--sub-text);
  font-size: 14px;
}
.vuln-container{
  border: 1px solid #e3e3e3;
  padding: 20px;
  border-radius: 15px;
  position: relative;
}

.exploit-btn{
  position: absolute;
  right: 20px;
  top: 20px;
}
</style>