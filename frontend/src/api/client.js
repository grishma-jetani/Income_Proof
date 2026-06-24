import axios from 'axios'
import { supabase } from '../lib/supabase'

const client = axios.create({
  baseURL: 'http://127.0.0.1:8000',
  timeout: 60000,
})

// Attach the current Supabase JWT to every request automatically
client.interceptors.request.use(async (config) => {
  const { data: { session } } = await supabase.auth.getSession()
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`
  }
  return config
})

// If the backend returns 401, sign the user out on the frontend too
client.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      await supabase.auth.signOut()
      window.location.href = '/'
    }
    return Promise.reject(error)
  }
)

export default client