<template>
  <div class="page-container">
    <el-card>
      <template #header>
        <div class="page-header">
          <span class="page-title">审核中心</span>
          <div class="header-actions">
            <el-tag type="danger" effect="dark" style="margin-right: 12px;">待处理: {{ pendingCount }}</el-tag>
            <el-select v-model="filterStatus" placeholder="状态筛选" clearable style="width: 140px; margin-right: 12px;" @change="loadData">
              <el-option label="待处理" value="待处理" />
              <el-option label="已解决" value="已解决" />
              <el-option label="已驳回" value="已驳回" />
            </el-select>
          </div>
        </div>
      </template>
      <el-alert
        title="审核规则：层位关系矛盾和重复编号问题须由专家处理后才能归档。只有专家或管理员可以处理审核。"
        type="warning"
        :closable="false"
        show-icon
        style="margin-bottom: 16px;"
      />
      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column label="类型" width="140">
          <template #default="{ row }">
            <el-tag v-if="row.audit_type === '层位矛盾'" type="warning" effect="dark">层位矛盾</el-tag>
            <el-tag v-else type="danger" effect="dark">重复编号</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="问题描述" min-width="280" show-overflow-tooltip />
        <el-table-column prop="related_ids" label="关联ID" width="140" />
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="resolution_note" label="处理说明" min-width="180" show-overflow-tooltip />
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column prop="resolved_at" label="处理时间" width="180" />
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              size="small"
              @click="openResolve(row)"
              :disabled="row.status !== '待处理'"
            >处理</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" title="处理审核" width="520px">
      <el-form label-width="100px">
        <el-form-item label="审核类型">
          <el-tag>{{ current.audit_type }}</el-tag>
        </el-form-item>
        <el-form-item label="问题描述">
          <span>{{ current.description }}</span>
        </el-form-item>
        <el-form-item label="处理结果">
          <el-radio-group v-model="resolveForm.status">
            <el-radio label="已解决">标记已解决</el-radio>
            <el-radio label="已驳回">驳回</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="处理说明">
          <el-input v-model="resolveForm.resolution_note" type="textarea" :rows="4" placeholder="请填写处理说明..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitResolve">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../utils/api'

const list = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const saving = ref(false)
const filterStatus = ref('')
const current = ref({})
const resolveForm = reactive({ status: '已解决', resolution_note: '' })

const pendingCount = computed(() => list.value.filter(x => x.status === '待处理').length)

const statusType = (status) => {
  const map = { '待处理': 'danger', '已解决': 'success', '已驳回': 'info' }
  return map[status] || 'info'
}

const loadData = async () => {
  loading.value = true
  try {
    const params = filterStatus.value ? { status: filterStatus.value } : {}
    list.value = await api.get('/audits', { params })
  } finally {
    loading.value = false
  }
}

const openResolve = (row) => {
  current.value = row
  resolveForm.status = '已解决'
  resolveForm.resolution_note = ''
  dialogVisible.value = true
}

const submitResolve = async () => {
  saving.value = true
  try {
    await api.put(`/audits/${current.value.id}`, resolveForm)
    ElMessage.success('处理成功')
    dialogVisible.value = false
    loadData()
  } finally {
    saving.value = false
  }
}

onMounted(loadData)
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
</style>
