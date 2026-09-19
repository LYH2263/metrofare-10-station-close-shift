<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getJSON } from '../api'
const route = useRoute()
const st = ref(null)
const load = async () => { st.value = await getJSON(`/api/stations/${route.params.code}`) }
onMounted(load); watch(() => route.params.code, load)
</script>
<template>
  <div class="page" v-if="st"><h1>{{ st.name }}</h1><p class="muted">编码 {{ st.code }}</p>
    <div v-if="st.closed" class="panel">
      <p><span class="closed-tag">已封闭</span></p>
      <p>封闭原因：{{ st.closed_reason || '—' }}</p>
      <p>改到站：<router-link :to="`/stations/${st.reroute_to}`">{{ st.reroute_to }}</router-link></p>
    </div>
    <p v-else class="muted">状态：正常</p>
  </div>
</template>
