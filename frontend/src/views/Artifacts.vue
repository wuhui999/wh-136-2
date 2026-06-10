<template>
  <div class="page-container">
    <el-card>
      <template #header>
        <div class="page-header">
          <span class="page-title">出土物管理</span>
          <div class="header-actions">
            <el-input
              v-model="searchKeyword"
              placeholder="搜索编号或类别"
              clearable
              style="width: 220px; margin-right: 12px;"
              @keyup.enter="handleSearch"
              @clear="handleSearch"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
            <el-select v-model="filterStratum" placeholder="按地层筛选" clearable style="width: 180px; margin-right: 12px;" @change="handleFilterChange">
              <el-option v-for="s in strata" :key="s.id" :label="s.code" :value="s.id" />
            </el-select>
            <el-select v-model="filterStatus" placeholder="按状态筛选" clearable style="width: 140px; margin-right: 12px;" @change="handleFilterChange">
              <el-option label="出土" value="出土" />
              <el-option label="清洗" value="清洗" />
              <el-option label="修复" value="修复" />
              <el-option label="入库" value="入库" />
              <el-option label="展出" value="展出" />
            </el-select>
            <el-button type="primary" :icon="Plus" @click="openDialog()" :disabled="!auth.isExcavator && !auth.isAdmin">新增出土物</el-button>
          </div>
        </div>
      </template>
      <el-alert
        title="出土物编号全局唯一。状态流转：出土 → 清洗 → 修复 → 入库 → 展出。整理员可更新状态。"
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 16px;"
      />
      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="code" label="出土物编号" width="150" />
        <el-table-column prop="category" label="类别" width="120" />
        <el-table-column label="所属层位" width="140">
          <template #default="{ row }">
            {{ getStratumCode(row.stratum_id) }}
          </template>
        </el-table-column>
        <el-table-column label="坐标" width="180">
          <template #default="{ row }">
            <span class="coord-text">X:{{ row.coord_x ?? '-' }} Y:{{ row.coord_y ?? '-' }} Z:{{ row.coord_z ?? '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="180" />
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="openDialog(row)" :disabled="!auth.isExcavator && !auth.isCurator && !auth.isAdmin">编辑</el-button>
            <el-button type="warning" link size="small" @click="changeStatus(row)" :disabled="!auth.isCurator && !auth.isAdmin">更新状态</el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row)" :disabled="!auth.isAdmin">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑出土物' : '新增出土物'" width="600px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="出土物编号" prop="code">
          <el-input v-model="form.code" :disabled="isEdit" placeholder="全局唯一编号，如：ART-2024-0001" />
        </el-form-item>
        <el-form-item label="类别">
          <el-input v-model="form.category" placeholder="如：陶器、石器、骨器" />
        </el-form-item>
        <el-form-item label="所属地层" prop="stratum_id">
          <el-select v-model="form.stratum_id" placeholder="选择地层" style="width: 100%;">
            <el-option-group v-for="t in trenches" :key="t.id" :label="t.code">
              <el-option v-for="s in getStrataByTrench(t.id)" :key="s.id" :label="s.code" :value="s.id" />
            </el-option-group>
          </el-select>
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="8">
            <el-form-item label="X坐标">
              <el-input-number v-model="form.coord_x" :precision="3" :step="0.1" :min="-9999" :max="9999" style="width: 100%;" controls-position="right" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="Y坐标">
              <el-input-number v-model="form.coord_y" :precision="3" :step="0.1" :min="-9999" :max="9999" style="width: 100%;" controls-position="right" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="Z坐标">
              <el-input-number v-model="form.coord_z" :precision="3" :step="0.1" :min="-9999" :max="9999" style="width: 100%;" controls-position="right" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="状态" v-if="isEdit">
          <el-select v-model="form.status" style="width: 100%;">
            <el-option label="出土" value="出土" />
            <el-option label="清洗" value="清洗" />
            <el-option label="修复" value="修复" />
            <el-option label="入库" value="入库" />
            <el-option label="展出" value="展出" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="statusDialogVisible" title="更新出土物状态" width="420px">
      <el-form label-width="80px">
        <el-form-item label="当前编号">
          <span>{{ currentArtifact?.code }}</span>
        </el-form-item>
        <el-form-item label="当前状态">
          <el-tag :type="statusType(currentArtifact?.status)">{{ currentArtifact?.status }}</el-tag>
        </el-form-item>
        <el-form-item label="下一状态">
          <el-select v-model="newStatus" placeholder="选择新状态" style="width: 100%;">
            <el-option v-for="s in availableStatuses" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="statusDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitStatus">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import api from '../utils/api'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const auth = useAuthStore()
const list = ref([])
const strata = ref([])
const trenches = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const statusDialogVisible = ref(false)
const saving = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const filterStratum = ref(route.query.stratum_id ? Number(route.query.stratum_id) : '')
const filterStatus = ref('')
const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const formRef = ref(null)
const currentArtifact = ref(null)
const newStatus = ref('')

const STATUS_FLOW = {
  '出土': ['清洗'],
  '清洗': ['修复', '入库'],
  '修复': ['入库', '展出'],
  '入库': ['展出'],
  '展出': ['入库']
}

const form = reactive({
  code: '',
  category: '',
  stratum_id: null,
  coord_x: 0,
  coord_y: 0,
  coord_z: 0,
  status: '出土',
  description: ''
})

const rules = {
  code: [{ required: true, message: '请输入出土物编号', trigger: 'blur' }],
  stratum_id: [{ required: true, message: '请选择地层', trigger: 'change' }]
}

const statusType = (status) => {
  const map = { '出土': 'info', '清洗': 'warning', '修复': '', '入库': 'success', '展出': 'primary' }
  return map[status] || 'info'
}

const availableStatuses = computed(() => {
  if (!currentArtifact.value) return []
  return STATUS_FLOW[currentArtifact.value.status] || []
})

const getStrataByTrench = (trenchId) => strata.value.filter(s => s.trench_id === trenchId)
const getStratumCode = (id) => {
  const s = strata.value.find(x => x.id === id)
  if (!s) return '-'
  const t = trenches.value.find(x => x.id === s.trench_id)
  return `${t?.code || ''} ${s.code}`.trim()
}

const loadData = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value
    }
    if (filterStratum.value) params.stratum_id = filterStratum.value
    if (filterStatus.value) params.status = filterStatus.value
    if (searchKeyword.value) params.keyword = searchKeyword.value
    const result = await api.get('/artifacts', { params })
    list.value = result.items
    total.value = result.total
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  loadData()
}

const handleFilterChange = () => {
  currentPage.value = 1
  loadData()
}

const handlePageChange = (val) => {
  currentPage.value = val
  loadData()
}

const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1
  loadData()
}

const loadStrata = async () => {
  strata.value = await api.get('/strata')
}

const loadTrenches = async () => {
  trenches.value = await api.get('/trenches')
}

const openDialog = (row = null) => {
  isEdit.value = !!row
  editId.value = row?.id || null
  Object.assign(form, {
    code: row?.code || '',
    category: row?.category || '',
    stratum_id: row?.stratum_id || filterStratum.value || null,
    coord_x: row?.coord_x ?? 0,
    coord_y: row?.coord_y ?? 0,
    coord_z: row?.coord_z ?? 0,
    status: row?.status || '出土',
    description: row?.description || ''
  })
  dialogVisible.value = true
}

const handleSubmit = async () => {
  await formRef.value.validate()
  saving.value = true
  try {
    if (isEdit.value) {
      await api.put(`/artifacts/${editId.value}`, form)
      ElMessage.success('更新成功')
    } else {
      await api.post('/artifacts', form)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadData()
  } finally {
    saving.value = false
  }
}

const changeStatus = (row) => {
  currentArtifact.value = row
  newStatus.value = availableStatuses.value[0] || ''
  statusDialogVisible.value = true
}

const submitStatus = async () => {
  if (!newStatus.value) {
    ElMessage.warning('请选择新状态')
    return
  }
  saving.value = true
  try {
    await api.put(`/artifacts/${currentArtifact.value.id}`, { status: newStatus.value })
    ElMessage.success('状态更新成功')
    statusDialogVisible.value = false
    loadData()
  } finally {
    saving.value = false
  }
}

const handleDelete = (row) => {
  ElMessageBox.confirm(`确定要删除出土物 ${row.code} 吗？`, '提示', { type: 'warning' })
    .then(async () => {
      await api.delete(`/artifacts/${row.id}`)
      ElMessage.success('删除成功')
      loadData()
    }).catch(() => {})
}

onMounted(async () => {
  await Promise.all([loadStrata(), loadTrenches()])
  loadData()
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
.coord-text {
  font-family: 'Consolas', monospace;
  font-size: 13px;
  color: #606266;
}
.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
