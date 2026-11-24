# Calculadora CI con Docker

API de calculadora (Flask) que guarda el historial de operaciones en PostgreSQL.
Son dos contenedores que se comunican por una red propia de Docker.

## Arquitectura

| Servicio | Imagen | Papel | Puerto |
|---|---|---|---|
| api | python:3.12-slim (Dockerfile propio) | Recibe operaciones y las guarda | 5000 |
| db | postgres:16.4-alpine | Guarda el historial en el volumen datos-db | 5432 (solo red interna) |

La API se conecta a la base de datos con el NOMBRE DEL SERVICIO `db` (variable `DB_HOST=db`), nunca con localhost ni con una IP fija.

## Estructura

- `app/Dockerfile`: imagen del servicio api
- `app/app.py`: API Flask
- `app/requirements.txt`: dependencias con version fija
- `calculadora.py`: operaciones reutilizadas por la API
- `docker-compose.yml`: servicios, red, volumen y variables
- `.env.example`: plantilla de variables (el `.env` real NO se sube)
- `.dockerignore`
- `.github/workflows/ci.yml`: pipeline de CI

## Como levantar los contenedores

    cp .env.example .env            # y cambie la contrasena en .env
    docker compose up -d --build    # construye y levanta api + db
    docker ps                       # verifica que ambos esten corriendo

## Probar la comunicacion (ida y vuelta)

    # Guardar una operacion (la API la escribe en PostgreSQL)
    curl -X POST localhost:5000/operaciones -H "Content-Type: application/json" -d '{"operacion":"sumar","a":2,"b":3}'

    # Leer el historial (la API lo consulta en PostgreSQL)
    curl localhost:5000/operaciones

    # Ver que la API resuelve el nombre del servicio db
    docker compose exec api getent hosts db

Operaciones disponibles: sumar, restar, multiplicar, dividir, potencia.

## Apagar

    docker compose down       # detiene los contenedores
    docker compose down -v    # ademas borra el volumen con los datos

## Integracion continua

GitHub Actions ejecuta las pruebas con pytest, construye las imagenes con `docker compose build`, levanta los contenedores y prueba la comunicacion en cada push y pull request.
