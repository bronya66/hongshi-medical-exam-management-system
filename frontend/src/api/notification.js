import request from './request'

export function getNotificationListApi(params) {
  return request({
    url: '/notification/list',
    method: 'get',
    params
  })
}

export function markNotificationReadApi(notificationId) {
  return request({
    url: `/notification/${notificationId}/read`,
    method: 'post'
  })
}

export function markAllNotificationReadApi() {
  return request({
    url: '/notification/read_all',
    method: 'post'
  })
}

export function getAdminNotificationListApi(params) {
  return request({
    url: '/admin/notification/list',
    method: 'get',
    params
  })
}

export function markAdminNotificationReadApi(notificationId) {
  return request({
    url: `/admin/notification/${notificationId}/read`,
    method: 'post'
  })
}

export function markAllAdminNotificationReadApi() {
  return request({
    url: '/admin/notification/read_all',
    method: 'post'
  })
}