# Calendario Atleta Híbrido España

Mapa y buscador de medias maratones y maratones de España. Web estática (GitHub Pages), sin servidor ni build: un `index.html` + `app.js` + Leaflet sobre `data/races.json`.

## Datos

El dataset se regenera cada 15 días con GitHub Actions (`.github/workflows/actualizar-datos.yml`):

1. `scripts/build_dataset.py --refresh` descarga las fuentes, normaliza, deduplica (por modalidad + fecha + ciudad/provincia), geocodifica (Nominatim, con caché en `data/geocache.json`) y genera `data/races.json`.
2. `scripts/check_official_sites.py` comprueba que la web oficial de cada carrera responde y que la fecha aparece en ella, y ajusta el nivel de validación.

Fuentes: carreraspopulares.com (API), Finishers, Runnea y Runner's World España (contraste editorial).

## Niveles de validación

- `confirmada_web_oficial`: la web oficial responde y muestra la fecha.
- `confirmada_organizacion`: una fuente la da por confirmada, o dos agendas coinciden.
- `fecha_estimada`: fecha aproximada sin confirmar.
- `por_verificar`: una sola agenda, o la web oficial no responde.

Si un dato no existe (precio, web oficial) se muestra como no disponible; nunca se inventa.

## Esquema de carrera

`{id, nombre, modalidad (medio_maraton|maraton), fecha, fecha_confirmada, ciudad, provincia, ccaa, lat, lng, precio, precio_texto, web_oficial, fuentes[], nivel_validacion, ultima_comprobacion, ubicacion_aproximada}`

El esquema es genérico por modalidad para poder añadir triatlón, Hyrox, 5k o 10k sin rehacer el pipeline.

## Uso local

```
python3 -m http.server 8000
# http://localhost:8000
```

## Modalidades y fuentes (fase 2)

El esquema sigue siendo genérico. `modalidad` admite `5k`, `10k`, `medio_maraton`, `maraton`, `triatlon_sprint`, `triatlon_olimpico`, `triatlon_media`, `triatlon_larga`, `hyrox`, `hibrida` y `obstaculos`.

Fuentes automáticas activas:

- Carreras Populares: 5K, 10K, media y maratón mediante su API.
- Finishers: páginas Next.js de 5K, 10K, media, maratón y triatlón. En triatlón se clasifica cada formato por distancia total publicada, no por el nombre del evento.
- Runnea: contraste adicional de 10K, media y maratón.
- HYROX: calendario y fichas oficiales.
- Hyatlón: calendario oficial del organizador.
- Spartan: solo fichas oficiales españolas descubiertas y verificables. No se infieren carreras desde ediciones pasadas.

Fuentes evaluadas pero no usadas para confirmar automáticamente:

- Hybrid Heroes: calendario legible y estable, pero es un gimnasio/proyecto local; sirve para descubrir eventos, no como confirmación bajo el criterio de entidad independiente.
- Calendario Carreras Obstáculos: HTML estable y estados explícitos, pero no identifica entidad responsable suficiente para elevar el nivel por sí solo.
- OCRA España: entidad válida, pero la página carga los datos dinámicamente y no expone un feed estable en CI.
- OCR Aragón: entidad válida, pero la protección anti-bot bloquea el cron.
- Ahotu: Cloudflare devuelve 403 desde servidores.
- FETRI Live: fuente institucional, pero es una aplicación Blazor orientada a resultados, sin calendario HTML/API estable consumible por el cron.

`data/races_full.json` conserva todos los niveles. `data/races.json` solo contiene `confirmada_web_oficial` o `confirmada_organizacion`.
