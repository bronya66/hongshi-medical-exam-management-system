// 注册等公开接口（无需登录）

import request from './request'

export function getPublicTeacherListApi() {
  return request({
    url: '/public/teacher_list',
    method: 'get'
  })
}
