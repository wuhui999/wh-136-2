<template>
  <div class="page-container">
    <el-card>
      <template #header>
        <div class="page-header">
          <span class="page-title">探方管理</span>
          <div class="header-actions">
            <el-select v-model="filterStatus" placeholder="状态筛选" clearable style="width: 140px; margin-right: 12px;" @change="loadData">
              <el-option label="发掘中" value="发掘中" />
              <el-option label="暂停" value="暂停" />
              <el-option label="完成" value="完成" />
              <el-option label="归档" value="归档" />
            </el-select>
            <el-button type="primary" :icon="Plus" @click="openDialog()">新增探方</el-button>
          </div>
        </div>
      </template>
      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="code" label="探方编号" width="140" />
        <el-table-column prop="location" label="位置" />
        <el-table-column label="负责人" width="140">
          <template #default="{ row }">
            {{ row.responsible_user?.full_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="strata_count" label="地层数" width="100" align="center" />
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="openDialog(row)">编辑</el-button>
            <el-button type="success" link size="small" @click="goToStrata(row)">地层</el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row)" v-if="auth.isAdmin">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑探方' : '新增探方'" width="560px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="探方编号" prop="code">
          <el-input v-model="form.code" :disabled="isEdit" placeholder="如：T001" />
        </el-form-item>
        <el-form-item label="位置" prop="location">
          <el-input v-model="form.location" placeholder="如：A区第3排" />
        </el-form-item>
        <el-form-item label="负责人" prop="responsible_user_id">
          <el-select v-model="form.responsible_user_id" placeholder="选择负责人" clearable style="width: 100%;">
            <el-option v-for="u in users" :key="u.id" :label="u.full_name || u.username" :value="u.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="form.status" style="width: 100%;">
            <el-option label="发掘中" value="发掘中" />
            <el-option label="暂停" value="暂停" />
            <el-option label="完成" value="完成" />
            <el-option label="归档" value="归档" />
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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import api from '../utils/api'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()
const list = ref([])
const users = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const saving = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const filterStatus = ref('')
const formRef = ref(null)

const form = reactive({
  code: '',
  location: '',
  responsible_user_id: null,
  status: '发掘中',
  description: ''
})

const rules = {
  code: [{ required: true, message: '请输入探方编号', trigger: 'blur' }]
}

const statusType = (status) => {
  const map = { '发掘中': 'primary', '暂停': 'warning', '完成': 'success', '归档': 'info' }
  return map[status] || 'info'
}

const loadData = async () => {
  loading.value = true
  try {
    list.value = await api.get('/trenches', { params: filterStatus.value ? { status: filterStatus.value } : {} })
  } finally {
    loading.value = false
  }
}

const loadUsers = async () => {
  try {
    users.value = await api.get('/auth/users')
  } catch {}
}

const openDialog = (row = null) => {
  isEdit.value = !!row
  editId.value = row?.id || null
  Object.assign(form, {
    code: row?.code || '',
    location: row?.location || '',
    responsible_user_id: row?.responsible_user_id || null,
    status: row?.status || '发掘中',
    description: row?.description || ''
  })
  dialogVisible.value = true
}

const handleSubmit = async () => {
  await formRef.value.validate()
  saving.value = true
  try {
    if (isEdit.value) {
      await api.put(`/trenches/${editId.value}`, form)
      ElMessage.success('更新成功')
    } else {
      await api.post('/trenches', form)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadData()
  } finally {
    saving.value = false
  }
}

const handleDelete = (row) => {
  ElMessageBox.confirm(`确定要删除探方 ${row.code} 吗？`, '提示', { type: 'warning' })
    .then(async () => {
      await api.delete(`/trenches/${row.id}`)
      ElMessage.success('删除成功')
      loadData()
    }).catch(() => {})
}

const goToStrata = (row) => {
  router.push({ path: '/strata', query: { trench_id: row.id } })
}

onMounted(() => {
  loadData()
  loadUsers()
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
</style>
