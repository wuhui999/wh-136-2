<template>
  <div class="page-container">
    <el-card>
      <template #header>
        <div class="page-header">
          <span class="page-title">地层管理</span>
          <div class="header-actions">
            <el-select v-model="filterTrench" placeholder="按探方筛选" clearable style="width: 180px; margin-right: 12px;" @change="loadData">
              <el-option v-for="t in trenches" :key="t.id" :label="t.code" :value="t.id" />
            </el-select>
            <el-button type="primary" :icon="Plus" @click="openDialog()" :disabled="!auth.isExcavator && !auth.isAdmin">新增地层</el-button>
          </div>
        </div>
      </template>
      <el-alert
        title="注意：删除地层前会自动检查是否有关联出土物，有关联则不允许删除"
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 16px;"
      />
      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="code" label="层位号" width="120" />
        <el-table-column label="所属探方" width="120">
          <template #default="{ row }">
            {{ getTrenchCode(row.trench_id) }}
          </template>
        </el-table-column>
        <el-table-column prop="soil_type" label="土质" width="120" />
        <el-table-column prop="estimated_age" label="年代推测" width="140" />
        <el-table-column label="深度范围" width="140">
          <template #default="{ row }">
            {{ row.depth_from != null ? row.depth_from : '-' }} ~ {{ row.depth_to != null ? row.depth_to : '-' }} m
          </template>
        </el-table-column>
        <el-table-column prop="order_index" label="层序" width="80" align="center" />
        <el-table-column prop="artifacts_count" label="出土物数" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.artifacts_count > 0" type="warning" size="small">{{ row.artifacts_count }}</el-tag>
            <span v-else class="text-muted">0</span>
          </template>
        </el-table-column>
        <el-table-column label="剖面照片" width="100">
          <template #default="{ row }">
            <el-link v-if="row.photo_url" :href="row.photo_url" target="_blank" type="primary" :underline="false">查看</el-link>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="openDialog(row)" :disabled="!auth.isExcavator && !auth.isAdmin">编辑</el-button>
            <el-button type="success" link size="small" @click="goToArtifacts(row)">出土物</el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row)" :disabled="!auth.isAdmin">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑地层' : '新增地层'" width="560px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="所属探方" prop="trench_id">
          <el-select v-model="form.trench_id" placeholder="选择探方" style="width: 100%;" :disabled="isEdit">
            <el-option v-for="t in trenches" :key="t.id" :label="t.code + ' - ' + (t.location || '')" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="层位号" prop="code">
          <el-input v-model="form.code" placeholder="如：第①层" />
        </el-form-item>
        <el-form-item label="土质">
          <el-input v-model="form.soil_type" placeholder="如：黄褐色黏土" />
        </el-form-item>
        <el-form-item label="年代推测">
          <el-input v-model="form.estimated_age" placeholder="如：新石器时代晚期" />
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="起始深度">
              <el-input-number v-model="form.depth_from" :precision="2" :step="0.1" style="width: 100%;" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="结束深度">
              <el-input-number v-model="form.depth_to" :precision="2" :step="0.1" style="width: 100%;" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="层序">
          <el-input-number v-model="form.order_index" :min="1" style="width: 50%;" />
        </el-form-item>
        <el-form-item label="剖面照片">
          <el-input v-model="form.photo_url" placeholder="照片URL地址" />
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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import api from '../utils/api'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const list = ref([])
const trenches = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const saving = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const filterTrench = ref(route.query.trench_id ? Number(route.query.trench_id) : '')
const formRef = ref(null)

const form = reactive({
  code: '',
  trench_id: null,
  soil_type: '',
  estimated_age: '',
  photo_url: '',
  description: '',
  depth_from: null,
  depth_to: null,
  order_index: null
})

const rules = {
  trench_id: [{ required: true, message: '请选择探方', trigger: 'change' }],
  code: [{ required: true, message: '请输入层位号', trigger: 'blur' }]
}

const getTrenchCode = (id) => trenches.value.find(t => t.id === id)?.code || '-'

const loadData = async () => {
  loading.value = true
  try {
    list.value = await api.get('/strata', { params: filterTrench.value ? { trench_id: filterTrench.value } : {} })
  } finally {
    loading.value = false
  }
}

const loadTrenches = async () => {
  trenches.value = await api.get('/trenches')
}

const openDialog = (row = null) => {
  isEdit.value = !!row
  editId.value = row?.id || null
  Object.assign(form, {
    code: row?.code || '',
    trench_id: row?.trench_id || filterTrench.value || null,
    soil_type: row?.soil_type || '',
    estimated_age: row?.estimated_age || '',
    photo_url: row?.photo_url || '',
    description: row?.description || '',
    depth_from: row?.depth_from ?? null,
    depth_to: row?.depth_to ?? null,
    order_index: row?.order_index ?? null
  })
  dialogVisible.value = true
}

const handleSubmit = async () => {
  await formRef.value.validate()
  saving.value = true
  try {
    if (isEdit.value) {
      await api.put(`/strata/${editId.value}`, form)
      ElMessage.success('更新成功')
    } else {
      await api.post('/strata', form)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadData()
  } finally {
    saving.value = false
  }
}

const handleDelete = (row) => {
  ElMessageBox.confirm(`确定要删除地层 ${row.code} 吗？删除前会检查关联出土物。`, '提示', { type: 'warning' })
    .then(async () => {
      await api.delete(`/strata/${row.id}`)
      ElMessage.success('删除成功')
      loadData()
    }).catch(() => {})
}

const goToArtifacts = (row) => {
  router.push({ path: '/artifacts', query: { stratum_id: row.id } })
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
.text-muted {
  color: #c0c4cc;
}
</style>
