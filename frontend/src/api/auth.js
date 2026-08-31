// 认证相关接口：登录、注册、退出

import request from './request'

export function loginApi(data) {
  return request({
    url: '/login',
    method: 'post',
    data
  })
}

export function registerApi(data) {
  return request({
    url: '/register',
    method: 'post',
    data
  })
}

export function logoutApi() {
  return request({
    url: '/logout',
    method: 'post'
  })
}
