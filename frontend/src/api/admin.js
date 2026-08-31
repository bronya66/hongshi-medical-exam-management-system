import request from './request'

export function adminLoginApi(data) {
	return request({ url: '/admin/login', method: 'post', data })
}

export function adminLogoutApi() {
	return request({ url: '/admin/logout', method: 'post' })
}

export function getAdminStatsApi() {
	return request({ url: '/admin/stats', method: 'get' })
}

export function getAdminUsersApi(params) {
	return request({ url: '/admin/users', method: 'get', params })
}

export function createAdminUserApi(data) {
	return request({ url: '/admin/users', method: 'post', data })
}

export function updateAdminUserApi(id, data) {
	return request({ url: `/admin/users/${id}`, method: 'put', data })
}

export function deleteAdminUserApi(id) {
	return request({ url: `/admin/users/${id}`, method: 'delete' })
}

export function getAdminAdminUsersApi(params) {
	return request({ url: '/admin/admin_users', method: 'get', params })
}

export function createAdminAdminUserApi(data) {
	return request({ url: '/admin/admin_users', method: 'post', data })
}

export function updateAdminAdminUserApi(id, data) {
	return request({ url: `/admin/admin_users/${id}`, method: 'put', data })
}

export function deleteAdminAdminUserApi(id) {
	return request({ url: `/admin/admin_users/${id}`, method: 'delete' })
}

export function getAdminStudentInfoListApi() {
	return request({ url: '/admin/student_info/list', method: 'get' })
}

export function createAdminStudentInfoApi(data) {
	return request({ url: '/admin/student_info', method: 'post', data })
}

export function updateAdminStudentInfoApi(id, data) {
	return request({ url: `/admin/student_info/${id}`, method: 'put', data })
}

export function deleteAdminStudentInfoApi(id) {
	return request({ url: `/admin/student_info/${id}`, method: 'delete' })
}

export function getAdminHomeworkListApi() {
	return request({ url: '/admin/homework/list', method: 'get' })
}

export function createAdminHomeworkApi(data) {
	return request({ url: '/admin/homework', method: 'post', data })
}

export function updateAdminHomeworkApi(id, data) {
	return request({ url: `/admin/homework/${id}`, method: 'put', data })
}

export function deleteAdminHomeworkApi(id) {
	return request({ url: `/admin/homework/${id}`, method: 'delete' })
}

export function getAdminMaterialsListApi() {
	return request({ url: '/admin/materials/list', method: 'get' })
}

export function createAdminMaterialsApi(data) {
	return request({ url: '/admin/materials', method: 'post', data })
}

export function updateAdminMaterialsApi(id, data) {
	return request({ url: `/admin/materials/${id}`, method: 'put', data })
}

export function deleteAdminMaterialsApi(id) {
	return request({ url: `/admin/materials/${id}`, method: 'delete' })
}

export function getAdminCheckinListApi() {
	return request({ url: '/admin/checkin/list', method: 'get' })
}

export function createAdminCheckinApi(data) {
	return request({ url: '/admin/checkin', method: 'post', data })
}

export function updateAdminCheckinApi(id, data) {
	return request({ url: `/admin/checkin/${id}`, method: 'put', data })
}

export function deleteAdminCheckinApi(id) {
	return request({ url: `/admin/checkin/${id}`, method: 'delete' })
}

export function getAdminEvaluationListApi() {
	return request({ url: '/admin/evaluation/list', method: 'get' })
}

export function createAdminEvaluationApi(data) {
	return request({ url: '/admin/evaluation', method: 'post', data })
}

export function updateAdminEvaluationApi(id, data) {
	return request({ url: `/admin/evaluation/${id}`, method: 'put', data })
}

export function deleteAdminEvaluationApi(id) {
	return request({ url: `/admin/evaluation/${id}`, method: 'delete' })
}

export function adminDeleteCheckinBatchApi(ids) {
	return request({ url: '/admin/checkin/delete_batch', method: 'post', data: { ids } })
}

export function adminDeleteHomeworkBatchApi(ids) {
	return request({ url: '/admin/homework/delete_batch', method: 'post', data: { ids } })
}

export function adminDeleteMaterialsBatchApi(ids) {
	return request({ url: '/admin/materials/delete_batch', method: 'post', data: { ids } })
}

export function adminDeleteEvaluationBatchApi(ids) {
	return request({ url: '/admin/evaluation/delete_batch', method: 'post', data: { ids } })
}

export function getAdminCheckinExportUrl() {
	return '/api/admin/checkin/export'
}

export function getAdminHomeworkExportUrl() {
	return '/api/admin/homework/export'
}

export function getAdminMaterialsExportUrl() {
	return '/api/admin/materials/export'
}

export function getAdminEvaluationExportUrl() {
	return '/api/admin/evaluation/export'
}
