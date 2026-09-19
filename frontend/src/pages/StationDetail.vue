<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getJSON, postJSON } from '../api'
const route = useRoute()
const st = ref(null)
const divertOptions = ref([])
const divertTo = ref('')
const reason = ref('')
const err = ref('')
const ok = ref('')

const showErr = (e) => {
  try { err.value = JSON.parse(e.message).detail || e.message }
  catch { err.value = e.message }
}

const load = async () => {
  err.value = ''; ok.value = ''
  const code = route.params.code
  st.value = await getJSON(`/api/stations/${code}`)
  const [open, edges] = await Promise.all([
    getJSON('/api/stations'),           // 默认只含未封闭站
    getJSON('/api/edges'),
  ])
  const adj = new Set()
  for (const e of edges.items) {
    if (e.a === code) adj.add(e.b)
    if (e.b === code) adj.add(e.a)
  }
  divertOptions.value = open.items.filter(s => adj.has(s.code))
  divertTo.value = divertOptions.value[0]?.code || ''
  reason.value = ''
}

const close = async () => {
  err.value = ''; ok.value = ''
  if (!divertTo.value) { err.value = '请选择改到站'; return }
  try {
    await postJSON(`/api/stations/${st.value.code}/close`, { divert_to: divertTo.value, reason: reason.value })
    ok.value = `已封闭，改到 ${divertTo.value}`
    await load()
  } catch (e) { showErr(e) }
}

const unclose = async () => {
  err.value = ''; ok.value = ''
  try {
    await postJSON(`/api/stations/${st.value.code}/unclose`, {})
    ok.value = '已解除封闭'
    await load()
  } catch (e) { showErr(e) }
}

onMounted(load); watch(() => route.params.code, load)
</script>
<template>
  <div class="page" v-if="st">
    <h1>{{ st.name }}</h1>
    <p class="muted">编码 {{ st.code }}</p>

    <div v-if="st.closed" class="panel">
      <p><span class="tag tag-closed">封闭中</span></p>
      <p>改到站：<strong>{{ st.divert_to }}</strong></p>
      <p>封闭原因：{{ st.closed_reason || '（未填写）' }}</p>
      <button @click="unclose">解除封闭</button>
    </div>

    <div v-else class="panel">
      <h3>封闭该站</h3>
      <p>
        改到站
        <select v-model="divertTo">
          <option v-for="s in divertOptions" :key="s.code" :value="s.code">{{ s.code }} {{ s.name }}</option>
        </select>
        原因
        <input v-model="reason" placeholder="如：台风停运" />
        <button @click="close">封闭</button>
      </p>
      <p v-if="!divertOptions.length" class="muted">无可用邻接站，无法封闭</p>
    </div>

    <p v-if="ok" class="ok">{{ ok }}</p>
    <p v-if="err" class="err">{{ err }}</p>
  </div>
</template>
