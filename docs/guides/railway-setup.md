# Railway

The full explanation of what deployment is, why there are two services, and the click-by-click setup is in [phases/09-deployment/README.md](../phases/09-deployment/README.md).

Short version:

1. Supabase already holds the data. Railway only runs the frontend and the backend.
2. Backend service root directory: `backend`. Public URL must answer `GET /health`.
3. Frontend service root directory: `frontend`. Set `VITE_*` variables before the build.
4. Add the frontend URL to backend `ALLOWED_ORIGINS`, then restart the backend.
5. Add that same URL under Supabase Authentication → URL configuration.
6. Smoke test in the browser: sign in, ask one cited question, reload.

Do not commit `.env` files. Paste secrets into Railway variables.
