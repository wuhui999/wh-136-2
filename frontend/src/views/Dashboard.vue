<template>
  <div>
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon icon-trench">
              <el-icon :size="36"><OfficeBuilding /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.trenches }}</div>
              <div class="stat-label">探方总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon icon-stratum">
              <el-icon :size="36"><Tickets /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.strata }}</div>
              <div class="stat-label">地层总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon icon-artifact">
              <el-icon :size="36"><Collection /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.artifacts }}</div>
              <div class="stat-label">出土物总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon icon-audit">
              <el-icon :size="36"><CircleCheck /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ pendingAudits }}</div>
              <div class="stat-label">待审核</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>最近出土物</span>
              <el-button type="primary" link @click="$router.push('/artifacts')">查看全部</el-button>
            </div>
          </template>
          <el-table :data="recentArtifacts" style="width: 100%" size="small">
            <el-table-column prop="code" label="编号" width="140" />
            <el-table-column prop="category" label="类别" width="100" />
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag size="small" :type="statusType(row.status)">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="录入时间" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>探方状态分布</span>
            </div>
          </template>
          <div class="trench-status">
            <div v-for="(count, status) in trenchStatusMap" :key="status" class="status-item">
              <div class="status-bar">
                <div class="status-fill" :style="{ width: (count / Math.max(totalTrenches, 1) * 100) + '%', background: trenchStatusColor[status] }"></div>
              </div>
              <div class="status-label">
                <span>{{ status }}</span>
                <span class="status-count">{{ count }}</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '../utils/api'

const stats = ref({ trenches: 0, strata: 0, artifacts: 0, users: 0 })
const recentArtifacts = ref([])
const pendingAudits = ref(0)
const trenches = ref([])

const statusType = (status) => {
  const map = { '出土': 'info', '清洗': 'warning', '修复': '', '入库': 'success', '展出': 'primary' }
  return map[status] || 'info'
}

const trenchStatusColor = {
  '发掘中': '#409EFF',
  '暂停': '#E6A23C',
  '完成': '#67C23A',
  '归档': '#909399'
}

const trenchStatusMap = computed(() => {
  const map = { '发掘中': 0, '暂停': 0, '完成': 0, '归档': 0 }
  trenches.value.forEach(t => { map[t.status] = (map[t.status] || 0) + 1 })
  return map
})

const totalTrenches = computed(() => Object.values(trenchStatusMap.value).reduce((a, b) => a + b, 0))

onMounted(async () => {
  stats.value = await api.get('/relations/stats')
  recentArtifacts.value = (await api.get('/artifacts')).slice(0, 5)
  const audits = await api.get('/audits', { params: { status: '待处理' } })
  pendingAudits.value = audits.length
  trenches.value = await api.get('/trenches')
})
</script>

<style scoped>
.stat-card {
  border-radius: 8px;
}
.stat-content {
  display: flex;
  align-items: center;
  gap: 20px;
}
.stat-icon {
  width: 70px;
  height: 70px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}
.icon-trench { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
.icon-stratum { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
.icon-artifact { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
.icon-audit { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }
.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
}
.stat-label {
  color: #909399;
  margin-top: 4px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}
.trench-status {
  padding: 10px 0;
}
.status-item {
  margin-bottom: 18px;
}
.status-item:last-child {
  margin-bottom: 0;
}
.status-bar {
  height: 8px;
  background: #f0f2f5;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 8px;
}
.status-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s;
}
.status-label {
  display: flex;
  justify-content: space-between;
  color: #606266;
  font-size: 13px;
}
.status-count {
  font-weight: 600;
}
</style>
