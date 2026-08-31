// 督学端接口

import request from './request'

export function getSupervisorStudentList(params) {
  return request({
    url: '/supervisor/student_list',
    method: 'get',
    params
  })
}

export function editSupervisorStudentApi(data) {
  return request({
    url: '/supervisor/edit_student',
    method: 'post',
    data
  })
}

export function deleteSupervisorStudentApi(studentInfoId) {
  return request({
    url: `/supervisor/student/${studentInfoId}`,
    method: 'delete'
  })
}

export function getSupervisorCheckinStat() {
  return request({
    url: '/supervisor/checkin_stat',
    method: 'get'
  })
}

export function getSupervisorEvaluationStat() {
  return request({
    url: '/supervisor/evaluation_stat',
    method: 'get'
  })
}

export function remindSupervisorUncheckedApi(data) {
  return request({
    url: '/supervisor/checkin_remind',
    method: 'post',
    data
  })
}
