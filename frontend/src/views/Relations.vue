<template>
  <div class="page-container">
    <el-card>
      <template #header>
        <div class="page-header">
          <span class="page-title">层位与出土物关联图</span>
          <div class="header-actions">
            <el-select v-model="filterTrench" placeholder="选择探方" clearable style="width: 200px; margin-right: 12px;" @change="loadData">
              <el-option v-for="t in trenches" :key="t.id" :label="t.code + ' - ' + (t.location || '')" :value="t.id" />
            </el-select>
            <el-button @click="loadData" :icon="Refresh">刷新</el-button>
          </div>
        </div>
      </template>

      <div class="legend">
        <div class="legend-item"><span class="legend-dot trench"></span>探方</div>
        <div class="legend-item"><span class="legend-dot stratum"></span>地层</div>
        <div class="legend-item"><span class="legend-dot artifact"></span>出土物</div>
      </div>

      <div class="graph-container" v-loading="loading">
        <div v-if="!graph.nodes.length" class="empty-tip">
          <el-empty description="暂无数据，请选择探方或先录入数据" />
        </div>
        <svg v-else :viewBox="viewBox" class="graph-svg">
          <defs>
            <marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
              <path d="M0,0 L0,6 L9,3 z" fill="#c0c4cc" />
            </marker>
          </defs>
          <g v-for="(edge, idx) in layout.edges" :key="'e'+idx">
            <line
              :x1="edge.sourceX" :y1="edge.sourceY"
              :x2="edge.targetX" :y2="edge.targetY"
              stroke="#c0c4cc" stroke-width="1.5"
              marker-end="url(#arrow)"
            />
            <text
              :x="(edge.sourceX + edge.targetX) / 2"
              :y="(edge.sourceY + edge.targetY) / 2 - 6"
              text-anchor="middle"
              fill="#909399"
              font-size="11"
            >{{ edge.label }}</text>
          </g>
          <g v-for="node in layout.nodes" :key="node.id" :transform="`translate(${node.x},${node.y})`" style="cursor: pointer;">
            <circle
              :r="nodeRadius(node)"
              :fill="nodeColor(node)"
              stroke="#fff"
              stroke-width="2"
              @mouseenter="hoverNode = node"
              @mouseleave="hoverNode = null"
            />
            <text
              text-anchor="middle"
              :y="4"
              fill="#fff"
              font-size="11"
              font-weight="500"
              style="pointer-events: none;"
            >{{ node.label }}</text>
          </g>
        </svg>
        <el-card v-if="hoverNode" class="tooltip">
          <div class="tooltip-title">{{ hoverNode.label }}</div>
          <div class="tooltip-type">类型：{{ typeLabel(hoverNode.type) }}</div>
          <div v-for="(v, k) in hoverNode.data" :key="k" class="tooltip-row">
            {{ k }}: {{ v }}
          </div>
        </el-card>
      </div>
    </el-card>

    <el-card style="margin-top: 20px;">
      <template #header>
        <span class="page-title">节点列表</span>
      </template>
      <el-row :gutter="20">
        <el-col :span="8" v-for="group in groupedNodes" :key="group.type">
          <h4>{{ typeLabel(group.type) }} ({{ group.nodes.length }})</h4>
          <el-table :data="group.nodes" size="small" max-height="300">
            <el-table-column prop="label" label="名称" />
          </el-table>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import api from '../utils/api'

const loading = ref(false)
const trenches = ref([])
const filterTrench = ref('')
const hoverNode = ref(null)
const graph = reactive({ nodes: [], edges: [] })

const nodeColor = (node) => {
  const map = { trench: '#667eea', stratum: '#f5576c', artifact: '#43e97b' }
  return map[node.type] || '#909399'
}

const nodeRadius = (node) => node.type === 'trench' ? 40 : node.type === 'stratum' ? 30 : 22

const typeLabel = (t) => ({ trench: '探方', stratum: '地层', artifact: '出土物' }[t] || t)

const layout = computed(() => {
  const nodes = []
  const edges = []
  let maxX = 0, maxY = 0

  const trenchNodes = graph.nodes.filter(n => n.type === 'trench')
  const stratumNodes = graph.nodes.filter(n => n.type === 'stratum')
  const artifactNodes = graph.nodes.filter(n => n.type === 'artifact')

  const nodePos = {}
  let colX = 60

  trenchNodes.forEach((n, i) => {
    const y = 80 + i * 100
    nodePos[n.id] = { x: colX, y }
    nodes.push({ ...n, x: colX, y })
    maxX = Math.max(maxX, colX)
    maxY = Math.max(maxY, y)
  })

  colX += 160
  stratumNodes.forEach((n, i) => {
    const y = 60 + i * 90
    nodePos[n.id] = { x: colX, y }
    nodes.push({ ...n, x: colX, y })
    maxX = Math.max(maxX, colX)
    maxY = Math.max(maxY, y)
  })

  colX += 180
  artifactNodes.forEach((n, i) => {
    const cols = Math.ceil(Math.sqrt(artifactNodes.length))
    const row = Math.floor(i / cols)
    const col = i % cols
    const y = 50 + row * 70
    const x = colX + col * 130
    nodePos[n.id] = { x, y }
    nodes.push({ ...n, x, y })
    maxX = Math.max(maxX, x)
    maxY = Math.max(maxY, y)
  })

  graph.edges.forEach(e => {
    const s = nodePos[e.source]
    const t = nodePos[e.target]
    if (s && t) {
      edges.push({
        sourceX: s.x, sourceY: s.y,
        targetX: t.x - 20, targetY: t.y,
        label: e.label
      })
    }
  })

  return { nodes, edges }
})

const viewBox = computed(() => {
  return `0 0 ${Math.max(800, layout.value.nodes.reduce((m, n) => Math.max(m, n.x), 0) + 200)} ${Math.max(500, layout.value.nodes.reduce((m, n) => Math.max(m, n.y), 0) + 100)}`
})

const groupedNodes = computed(() => [
  { type: 'trench', nodes: graph.nodes.filter(n => n.type === 'trench') },
  { type: 'stratum', nodes: graph.nodes.filter(n => n.type === 'stratum') },
  { type: 'artifact', nodes: graph.nodes.filter(n => n.type === 'artifact') }
])

const loadTrenches = async () => {
  trenches.value = await api.get('/trenches')
}

const loadData = async () => {
  loading.value = true
  try {
    const params = filterTrench.value ? { trench_id: filterTrench.value } : {}
    const data = await api.get('/relations/graph', { params })
    graph.nodes = data.nodes
    graph.edges = data.edges
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadTrenches().then(loadData)
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.page-title {
  font-size: 16px;
  font-weight: 600;
}
.legend {
  display: flex;
  gap: 24px;
  margin-bottom: 16px;
  padding: 10px 16px;
  background: #f5f7fa;
  border-radius: 6px;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #606266;
}
.legend-dot {
  display: inline-block;
  width: 14px;
  height: 14px;
  border-radius: 50%;
}
.legend-dot.trench { background: #667eea; }
.legend-dot.stratum { background: #f5576c; }
.legend-dot.artifact { background: #43e97b; }
.graph-container {
  position: relative;
  min-height: 500px;
  background: #fafbfc;
  border-radius: 8px;
  overflow: auto;
}
.graph-svg {
  width: 100%;
  min-height: 500px;
}
.empty-tip {
  padding: 60px 0;
}
.tooltip {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 260px;
  font-size: 13px;
}
.tooltip-title {
  font-weight: 600;
  margin-bottom: 8px;
  color: #303133;
}
.tooltip-type {
  color: #909399;
  margin-bottom: 6px;
}
.tooltip-row {
  color: #606266;
  line-height: 1.8;
}
h4 {
  margin: 0 0 10px;
  color: #606266;
  font-size: 14px;
}
</style>
