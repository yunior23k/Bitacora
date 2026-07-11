# Bitácora de Apuestas — App independiente

App Flask con base de datos real (no se borra en cada reinicio de Render). Mismo flujo que ya usaste con tu MLB Analyzer, con un paso extra: la base de datos vive en Supabase (gratis, sin vencimiento), no en el disco de Render.

## Por qué Supabase y no solo Render

Render en su plan gratis borra el disco local en cada reinicio/deploy. Supabase da una base de datos Postgres gratuita que persiste indefinidamente, sin costo, y sin necesidad de tarjeta.

## Pasos

### 1. Crear la base de datos (Supabase, 5 min)
1. Ve a https://supabase.com y crea una cuenta gratis (puedes usar tu GitHub).
2. Crea un nuevo proyecto (elige cualquier nombre, ej. "bitacora-apuestas", y una contraseña para la base de datos — guárdala).
3. Una vez creado, ve a **Project Settings → Database → Connection string → URI**.
4. Copia esa URL (se ve algo así: `postgresql://postgres:[TU-PASSWORD]@db.xxxxx.supabase.co:5432/postgres`). Reemplaza `[TU-PASSWORD]` con la contraseña que pusiste.

### 2. Subir el código a GitHub
1. Crea un repo nuevo en GitHub (puede ser privado).
2. Sube estos archivos: `app.py`, `requirements.txt`, `templates/index.html`, `static/manifest.json`, `static/sw.js`, `static/icon-192.png`, `static/icon-512.png`.

### 3. Desplegar en Render (igual que tu MLB Analyzer)
1. En Render, "New +" → "Web Service" → conecta tu repo de GitHub.
2. Build command: `pip install -r requirements.txt`
3. Start command: `gunicorn app:app`
4. En la sección **Environment**, agrega una variable:
   - Key: `DATABASE_URL`
   - Value: la URL de Supabase que copiaste en el paso 1.
5. Deploy. Render te da una URL tipo `https://bitacora-apuestas.onrender.com`.

### 4. Instalarla en tu celular como app real
1. Abre esa URL en Chrome (Android) o Safari (iPhone).
2. Android: menú (⋮) → "Agregar a pantalla de inicio" / "Instalar app".
3. iPhone: botón compartir (□↑) → "Agregar a pantalla de inicio".
4. Te queda un ícono como cualquier otra app — abre a pantalla completa, sin barra de navegador.

## Notas
- El free tier de Render "duerme" el servicio tras ~15 min sin uso; la primera carga del día puede tardar unos segundos en despertar. Los datos NO se pierden con esto porque viven en Supabase, no en Render.
- Si más adelante quieres backups, Supabase permite exportar la base de datos desde su dashboard.
