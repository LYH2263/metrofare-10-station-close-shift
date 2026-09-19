<script setup>
import { computed, onMounted, ref } from 'vue'
import { getJSON, postJSON } from '../api'
const items = ref([])
const edges = ref([])
const closing = ref(null)
const rerouteTo = ref('')
const reason = ref('')
const error = ref('')
const load = async () => {
  items.value = (await getJSON('/api/stations?include_closed=true')).items
  edges.value = (await getJSON('/api/edges')).items
}
onMounted(load)
const openStations = computed(() => items.value.filter(s => !s.closed))
const neighborsOf = (code) => {
  const set = new Set()
  for (const e of edges.value) {
    if (e.a === code) set.add(e.b)
    if (e.b === code) set.add(e.a)
  }
  return openStations.value.filter(s => set.has(s.code))
}
const startClose = (s) => { closing.value = s.code; rerouteTo.value = ''; reason.value = ''; error.value = '' }
const confirmClose = async (s) => {
  try {
    await postJSON(`/api/stations/${s.code}/close`, { reroute_to: rerouteTo.value, reason: reason.value })
    closing.value = null
    await load()
  } catch (e) { error.value = e.message }
}
const unclose = async (s) => {
  try { await postJSON(`/api/stations/${s.code}/unclose`, {}); await load() }
  catch (e) { error.value = e.message }
}
</script>
<template>
  <div class="page"><h1>站点</h1>
    <p v-if="error" class="err">{{ error }}</p>
    <table>
      <tr><th>编码</th><th>名称</th><th>状态</th><th></th></tr>
      <template v-for="s in items" :key="s.code">
        <tr>
          <td>{{ s.code }}</td><td>{{ s.name }}</td>
          <td>
            <span v-if="s.closed" class="closed-tag">已封闭 → {{ s.reroute_to }}</span>
            <span v-else class="muted">正常</span>
          </td>
          <td>
            <router-link :to="`/stations/${s.code}`">详情</router-link>
            <a v-if="!s.closed" href="#" @click.prevent="startClose(s)">封闭</a>
            <a v-else href="#" @click.prevent="unclose(s)">解除封闭</a>
          </td>
        </tr>
        <tr v-if="closing === s.code">
          <td colspan="4">
            <div class="close-form">
              改到站
              <select v-model="rerouteTo">
                <option value="" disabled>选择邻接站</option>
                <option v-for="n in neighborsOf(s.code)" :key="n.code" :value="n.code">{{ n.code }} {{ n.name }}</option>
              </select>
              原因 <input v-model="reason" placeholder="封闭原因" />
              <button @click="confirmClose(s)">确认封闭</button>
              <button @click="closing = null">取消</button>
            </div>
          </td>
        </tr>
      </template>
    </table>
  </div>
</template>
