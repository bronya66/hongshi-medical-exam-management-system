// 任课老师端接口

import request from './request'

export function getTeacherStudentList() {
  return request({
    url: '/teacher/student_list',
    method: 'get'
  })
}

export function publishHomeworkApi(data) {
  return request({
    url: '/teacher/publish_homework',
    method: 'post',
    data,
    ...(data instanceof FormData
      ? {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      : {})
  })
}

export function getTeacherHomeworkListApi() {
  return request({
    url: '/teacher/homework_list',
    method: 'get'
  })
}

export function updateTeacherHomeworkApi(id, data) {
  return request({
    url: `/teacher/homework/${id}`,
    method: 'put',
    data,
    ...(data instanceof FormData
      ? {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      : {})
  })
}

export function deleteTeacherHomeworkApi(id) {
  return request({
    url: `/teacher/homework/${id}`,
    method: 'delete'
  })
}

export function getTeacherHomeworkSubmissionListApi(params) {
  return request({
    url: '/teacher/homework_submission_list',
    method: 'get',
    params
  })
}

export function reviewTeacherHomeworkSubmissionApi(id, data) {
  return request({
    url: `/teacher/homework_submission/${id}/review`,
    method: 'put',
    data
  })
}

export function uploadMaterialsApi(formData, onUploadProgress) {
  return request({
    url: '/teacher/upload_materials',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    onUploadProgress
  })
}

export function getTeacherMaterialsListApi() {
  return request({
    url: '/teacher/materials_list',
    method: 'get'
  })
}

export function updateTeacherMaterialsApi(id, data) {
  return request({
    url: `/teacher/materials/${id}`,
    method: 'put',
    data
  })
}

export function deleteTeacherMaterialsApi(id) {
  return request({
    url: `/teacher/materials/${id}`,
    method: 'delete'
  })
}

export function getTeacherEvaluationList() {
  return request({
    url: '/teacher/evaluation_list',
    method: 'get'
  })
}

export function getTeacherProfileApi() {
  return request({
    url: '/teacher/profile',
    method: 'get'
  })
}

export function updateTeacherProfileApi(data) {
  return request({
    url: '/teacher/profile',
    method: 'put',
    data
  })
}

export function getTeacherLearningPlanOverviewApi() {
  return request({
    url: '/teacher/learning_plan_overview',
    method: 'get'
  })
}

export function importTeacherLearningPlanTemplateApi(data) {
  return request({
    url: '/teacher/learning_plan_template_import',
    method: 'post',
    data
  })
}

export function createTeacherLearningTaskApi(data) {
  return request({
    url: '/teacher/learning_task',
    method: 'post',
    data
  })
}

export function getTeacherStudentLearningPlanDetailApi(studentId) {
  return request({
    url: '/teacher/student_learning_plan_detail',
    method: 'get',
    params: { student_id: studentId }
  })
}

export function getTeacherExamQuestionBankMetaApi() {
  return request({
    url: '/teacher/exam_question_bank_meta',
    method: 'get'
  })
}

export function generateTeacherExamQuestionsApi(data) {
  return request({
    url: '/teacher/exam_question_bank_generate',
    method: 'post',
    data
  })
}

// 考试模拟
export function createTeacherExamApi(data) {
  return request({
    url: '/teacher/exam',
    method: 'post',
    data
  })
}

export function getTeacherExamListApi() {
  return request({
    url: '/teacher/exam_list',
    method: 'get'
  })
}

export function getTeacherExamDetailApi(examId) {
  return request({
    url: `/teacher/exam/${examId}/detail`,
    method: 'get'
  })
}

export function deleteTeacherExamApi(examId) {
  return request({
    url: `/teacher/exam/${examId}`,
    method: 'delete'
  })
}

export function updateTeacherExamStatusApi(examId, status) {
  return request({
    url: `/teacher/exam/${examId}/status`,
    method: 'put',
    data: { status }
  })
}

export function getTeacherExamRecordListApi(examId) {
  return request({
    url: `/teacher/exam/${examId}/records`,
    method: 'get'
  })
}

export function getTeacherExamRecordDetailApi(recordId) {
  return request({
    url: `/teacher/exam_record/${recordId}/detail`,
    method: 'get'
  })
}

export function manualGradeTeacherExamRecordApi(recordId, data) {
  return request({
    url: `/teacher/exam_record/${recordId}/manual_grade`,
    method: 'put',
    data
  })
}

export function approveRetakeTeacherExamRecordApi(recordId) {
  return request({
    url: `/teacher/exam_record/${recordId}/approve_retake`,
    method: 'put'
  })
}

export function getTeacherExamRetakeRequestListApi(params) {
  return request({
    url: '/teacher/exam_retake_requests',
    method: 'get',
    params
  })
}

export function reviewTeacherExamRetakeRequestApi(requestId, data) {
  return request({
    url: `/teacher/exam_retake_request/${requestId}/review`,
    method: 'put',
    data
  })
}
