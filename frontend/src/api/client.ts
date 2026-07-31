import axios from "axios";

// Local dev / same-origin deployments (nginx proxy, docker-compose.prod.yml)
// use the relative path, which the dev server/nginx proxies to the
// backend. GitHub Pages serves pure static files with no proxy, so that
// deployment sets VITE_API_BASE_URL to the full Render backend URL at
// build time instead (see .github/workflows/deploy-pages.yml).
const baseURL = import.meta.env.VITE_API_BASE_URL || "/api/v1";

export const api = axios.create({
  baseURL,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("role");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);
