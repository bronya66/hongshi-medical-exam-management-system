<template>
  <!-- 根组件仅承载路由视图 -->
  <el-config-provider :locale="zhCn">
    <router-view />
  </el-config-provider>
</template>

<script setup>
// 根组件保持轻量，所有功能由路由页面承接
import zhCn from 'element-plus/es/locale/lang/zh-cn'
</script>
