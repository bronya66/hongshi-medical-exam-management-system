// 学员端接口

import request from './request'

export function getStudentProfileApi() {
  return request({
    url: '/student/profile',
    method: 'get'
  })
}

export function updateStudentProfileApi(data) {
  return request({
    url: '/student/profile',
    method: 'put',
    data
  })
}

export function getStudentCheckinListApi() {
  return request({
    url: '/student/checkin_list',
    method: 'get'
  })
}

export function getStudentTeacherListApi() {
  return request({
    url: '/student/teacher_list',
    method: 'get'
  })
}

export function getStudentHomeworkList() {
  return request({
    url: '/student/homework_list',
    method: 'get'
  })
}

export function submitStudentHomeworkApi(formData, onUploadProgress) {
  return request({
    url: '/student/homework_submit',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    onUploadProgress
  })
}

export function getStudentMaterialsList() {
  return request({
    url: '/student/materials_list',
    method: 'get'
  })
}

export function downloadMaterialsApi(materialId) {
  return request({
    url: '/student/download_materials',
    method: 'post',
    data: { material_id: materialId }
  })
}

export function studentCheckinApi(formData, onUploadProgress) {
  return request({
    url: '/student/checkin',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    onUploadProgress
  })
}

export function updateStudentCheckinApi(id, formData, onUploadProgress) {
  return request({
    url: `/student/checkin/${id}`,
    method: 'put',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    onUploadProgress
  })
}

export function deleteStudentCheckinApi(id) {
  return request({
    url: `/student/checkin/${id}`,
    method: 'delete'
  })
}

export function evaluateTeacherApi(data) {
  return request({
    url: '/student/evaluate_teacher',
    method: 'post',
    data
  })
}

export function getStudentEvaluationListApi() {
  return request({
    url: '/student/evaluation_list',
    method: 'get'
  })
}

export function updateStudentEvaluationApi(id, data) {
  return request({
    url: `/student/evaluation/${id}`,
    method: 'put',
    data
  })
}

export function deleteStudentEvaluationApi(id) {
  return request({
    url: `/student/evaluation/${id}`,
    method: 'delete'
  })
}

export function getStudentLearningPlanListApi() {
  return request({
    url: '/student/learning_plan_list',
    method: 'get'
  })
}

export function createStudentLearningPlanApi(data) {
  return request({
    url: '/student/learning_plan',
    method: 'post',
    data
  })
}

export function updateStudentLearningPlanApi(id, data) {
  return request({
    url: `/student/learning_plan/${id}`,
    method: 'put',
    data
  })
}

export function deleteStudentLearningPlanApi(id) {
  return request({
    url: `/student/learning_plan/${id}`,
    method: 'delete'
  })
}

export function getStudentLearningTaskListApi(planId) {
  return request({
    url: '/student/learning_task_list',
    method: 'get',
    params: { plan_id: planId }
  })
}

export function createStudentLearningTaskApi(data) {
  return request({
    url: '/student/learning_task',
    method: 'post',
    data
  })
}

export function updateStudentLearningTaskApi(id, data) {
  return request({
    url: `/student/learning_task/${id}`,
    method: 'put',
    data
  })
}

export function deleteStudentLearningTaskApi(id) {
  return request({
    url: `/student/learning_task/${id}`,
    method: 'delete'
  })
}

export function upsertStudentPlanProgressApi(data) {
  return request({
    url: '/student/plan_progress',
    method: 'post',
    data
  })
}

export function getStudentPlanProgressStatApi(planId) {
  return request({
    url: '/student/plan_progress_stat',
    method: 'get',
    params: { plan_id: planId }
  })
}

// 考试模拟
export const getStudentExamListApi = () =>
  request({
    url: '/student/exam_list',
    method: 'get'
  })

export const getStudentExamDetailApi = (examId) =>
  request({
    url: `/student/exam/${examId}/detail`,
    method: 'get'
  })

export const submitStudentExamApi = (data) =>
  request({
    url: '/student/exam_submit',
    method: 'post',
    data
  })

export const getStudentExamRecordListApi = () =>
  request({
    url: '/student/exam_record_list',
    method: 'get'
  })

export const getStudentExamRecordDetailApi = (recordId) =>
  request({
    url: `/student/exam_record/${recordId}/detail`,
    method: 'get'
  })

export const submitStudentExamRetakeRequestApi = (data) =>
  request({
    url: '/student/exam_retake_request',
    method: 'post',
    data
  })

// 资源推荐
export function getStudentRecommendationFeedApi() {
  return request({
    url: '/student/recommendation_feed',
    method: 'get'
  })
}
