import axios from 'axios';
const api=axios.create({baseURL:import.meta.env.VITE_API_BASE_URL||'http://127.0.0.1:8000/api/',headers:{'Content-Type':'application/json'}});
api.interceptors.request.use(c=>{const t=localStorage.getItem('access_token');if(t)c.headers.Authorization=`Bearer ${t}`;return c});
export const list=d=>Array.isArray(d)?d:(d?.results||d?.data||[]);
export async function login(username,password){const {data}=await api.post('auth/login/',{username,password});if(!data.access)throw Error('No access token returned');localStorage.setItem('access_token',data.access);if(data.refresh)localStorage.setItem('refresh_token',data.refresh);return data}
export const me=async()=>(await api.get('auth/me/')).data;
export const register=async p=>(await api.post('auth/register/',p)).data;
export const clubs=async()=>list((await api.get('clubs/')).data);
export const venues=async()=>list((await api.get('venues/')).data);
export const myEvents=async()=>list((await api.get('events/my/')).data);
export const pending=async()=>list((await api.get('approvals/pending/')).data);
export const calendar=async()=>list((await api.get('calendar/events/')).data);
export const notifications=async()=>list((await api.get('notifications/')).data);
export const createEvent=async p=>(await api.post('events/',p)).data;
export const approve=async id=>(await api.post(`events/${id}/approve/`,{})).data;
export const reject=async id=>(await api.post(`events/${id}/reject/`,{})).data;
export function logout(){['access_token','refresh_token','current_user'].forEach(k=>localStorage.removeItem(k))}
export default api;