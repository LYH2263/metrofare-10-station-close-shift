<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'
const items = ref([])
onMounted(async () => { items.value = (await getJSON('/api/stations?include_closed=1')).items })
</script>
<template>
  <div class="page"><h1>站点</h1>
    <table>
      <tr><th>编码</th><th>名称</th><th>状态</th><th></th></tr>
      <tr v-for="s in items" :key="s.code">
        <td>{{ s.code }}</td><td>{{ s.name }}</td>
        <td>
          <span v-if="s.closed" class="tag tag-closed">封闭 → {{ s.divert_to }}</span>
          <span v-else class="muted">正常</span>
        </td>
        <td><router-link :to="`/stations/${s.code}`">详情</router-link></td>
      </tr>
    </table>
  </div>
</template>
