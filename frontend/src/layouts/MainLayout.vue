<template>
  <el-container class="main-container">
    <el-aside width="220px" class="sidebar">
      <div class="logo">
        <el-icon :size="28" color="#fff"><Histogram /></el-icon>
        <span>考古记录系统</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <span>首页概览</span>
        </el-menu-item>
        <el-menu-item index="/trenches">
          <el-icon><OfficeBuilding /></el-icon>
          <span>探方管理</span>
        </el-menu-item>
        <el-menu-item index="/strata">
          <el-icon><Tickets /></el-icon>
          <span>地层管理</span>
        </el-menu-item>
        <el-menu-item index="/artifacts">
          <el-icon><Collection /></el-icon>
          <span>出土物管理</span>
        </el-menu-item>
        <el-menu-item index="/relations">
          <el-icon><Share /></el-icon>
          <span>关联图</span>
        </el-menu-item>
        <el-menu-item index="/audits" v-if="auth.isExpert">
          <el-icon><CircleCheck /></el-icon>
          <span>审核中心</span>
        </el-menu-item>
        <el-menu-item index="/users" v-if="auth.isAdmin">
          <el-icon><User /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <div class="header-left">
          <span>{{ $route.meta.title || '考古发掘记录系统' }}</span>
        </div>
        <div class="header-right">
          <el-tag size="small" :type="roleTagType">{{ roleLabel }}</el-tag>
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <el-avatar :size="32" style="margin-right: 8px;">
                {{ auth.user?.full_name?.charAt(0) || auth.user?.username?.charAt(0) }}
              </el-avatar>
              {{ auth.user?.full_name || auth.user?.username }}
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人信息</el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const activeMenu = computed(() => route.path)

const roleMap = {
  admin: { label: '管理员', type: 'danger' },
  expert: { label: '专家', type: 'warning' },
  curator: { label: '整理员', type: 'success' },
  excavator: { label: '发掘员', type: 'primary' }
}

const roleLabel = computed(() => roleMap[auth.userRole]?.label || auth.userRole)
const roleTagType = computed(() => roleMap[auth.userRole]?.type || 'info')

const handleCommand = (cmd) => {
  if (cmd === 'logout') {
    auth.logout()
    router.push('/login')
  }
}
</script>

<style scoped>
.main-container {
  height: 100vh;
}
.sidebar {
  background-color: #304156;
}
.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: #fff;
  font-size: 18px;
  font-weight: 600;
  border-bottom: 1px solid #1f2d3d;
}
.logo span {
  margin-left: 6px;
}
.sidebar .el-menu {
  border-right: none;
}
.header {
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}
.header-left {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}
.user-info {
  display: flex;
  align-items: center;
  cursor: pointer;
  color: #606266;
}
.main-content {
  background: #f0f2f5;
  padding: 20px;
  overflow-y: auto;
}
</style>
