<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'
const rows = ref([])
const parse = (h) => {
  let input = {}, result = {}
  try { input = JSON.parse(h.input_json) } catch { /* ignore */ }
  try { result = JSON.parse(h.result_json) } catch { /* ignore */ }
  return { ...h, input, result }
}
onMounted(async () => { rows.value = (await getJSON('/api/history')).items.map(parse) })
</script>
<template>
  <div class="page"><h1>试算记录</h1>
    <table>
      <tr><th>#</th><th>请求</th><th>实际使用</th><th>站数</th><th>票价</th><th>时间</th></tr>
      <tr v-for="h in rows" :key="h.id">
        <td>#{{ h.id }}</td>
        <td>{{ h.input.start }} → {{ h.input.end }}</td>
        <td>
          {{ h.result.actual_start ?? h.result.start }} → {{ h.result.actual_end ?? h.result.end }}
          <span v-if="h.result.diverted" class="tag tag-divert">改道</span>
        </td>
        <td>{{ h.result.hops }}</td>
        <td>{{ h.result.fare != null ? '¥' + h.result.fare : '' }}</td>
        <td class="muted">{{ h.created_at }}</td>
      </tr>
    </table>
  </div>
</template>
