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
