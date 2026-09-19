<script setup>
import { onMounted, ref } from 'vue'
import { getJSON, postJSON } from '../api'
const stations = ref([])
const start = ref('A1')
const end = ref('B2')
const out = ref(null)
onMounted(async () => { stations.value = (await getJSON('/api/stations')).items })
// 只读试算：persist=false，不落库
const run = async () => { out.value = await postJSON('/api/quote', { start: start.value, end: end.value, persist: false }) }
</script>
<template>
  <div class="page"><h1>最短站数票价</h1>
    <div class="panel">
      <select v-model="start"><option v-for="s in stations" :key="s.code" :value="s.code">{{ s.name }}</option></select>
      →
      <select v-model="end"><option v-for="s in stations" :key="s.code" :value="s.code">{{ s.name }}</option></select>
      <button @click="run">试算</button>
    </div>
    <div v-if="out" class="panel">
      <template v-if="out.reachable">
        <p>站数 {{ out.hops }} · 票价 <span class="hero-num">¥{{ out.fare }}</span></p>
        <p v-if="out.path" class="muted">途经 {{ out.path.join(' → ') }}</p>
        <p v-if="out.diverted" class="tag tag-divert">
          <template v-if="out.actual_start !== out.start">起点 {{ out.start }} 已封闭，已改到 {{ out.actual_start }} 站。</template>
          <template v-if="out.actual_end !== out.end">终点 {{ out.end }} 已封闭，已改到 {{ out.actual_end }} 站。</template>
        </p>
      </template>
      <p v-else class="muted">不可达</p>
    </div>
  </div>
</template>
