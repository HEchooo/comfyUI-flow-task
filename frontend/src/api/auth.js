import http from './http'

export async function login(payload) {
  const { data } = await http.post('/auth/login', payload)
  return data
}

export async function fetchMe() {
  const { data } = await http.get('/auth/me')
  return data
}
