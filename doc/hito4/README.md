# Hito 4: Composición de servicios

Para este hito, se pide la construcción de la infraestructura de la aplicación utilizando contenedores, de manera que sea deplegable de manera repetible en cualquier entorno.

## Estado del proyecto antes del hito
La infraestructura del proyecto ya estaba diseñada con contenedores desde la base, tanto la ejecución del backend como la base de datos y los tests. Para ello, utilizo dos archivos de docker compose: `docker-compose.yml` y `docker-compose.test.yml`.

Como sugiere el nombre, el segundo es el que levanta una instancia de pruebas de la aplicación y ejecuta los tests en un entorno efímero, creando una base de datos de pruebas que se elimina tras cada ejecución del contenedor. Este proceso ya se explicó en el [hito 2](../hito2/README.md).

Durante el desarrollo de este hito, comprobaré la dockerización ya montada, y refactorizaré lo necesario para cumplir con los requisitos del hito, además de documentar lo ya construido y el proceso de los cambios realizados.

## Estructura del clúster de contenedores
Para el despliegue de la aplicación, he utilizado 2 contenedores. El archivo `docker-compose.yml` que los gestiona es el siguiente:

```yml
services:
  db:
    image: postgres:15
    container_name: playtracker-db
    restart: always
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  backend:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: playtracker-backend
    restart: always
    depends_on:
      - db
    environment:
      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
    ports:
      - "8000:8000"
    command: >
      uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - ./:/app

volumes:
  pgdata:
```

#### Servicio de base de datos

```yml
  db:
    image: postgres:15
    container_name: playtracker-db
    restart: always
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
```

Mi base de datos es PostgreSQL, por lo que para el contenedor de base de datos he utilizado la [imagen oficial de postgres](https://hub.docker.com/_/postgres). En concreto, la versión 15, que es la que he utilizado en otros proyectos sin problemas. Es importante utilizar una versión fija de una imagen y no la etiqueta `latest`, ya que así garantizamos estabilidad y no tenemos problemas de actualizaciones automáticas no deseadas que rompan la aplicación.

He utilizado la **política de reinicio** `always` para reiniciar el contenedor automáticamente en caso de fallo.

En **environment** se especifica la configuración que se inyecta en el contendor al arrancarlo. Las variables necesarias para el contenedor se especifican en la [documentación de la imagen](https://hub.docker.com/_/postgres). Para no proporcionar datos sensibles en archivos públicos, las credenciales de la base de datos se extraen del archivo `.env` (uso de ${variable}).

Como **mapeo de puertos**, he asociado el puerto 5432 del host al mismo puerto del contenedor. Es el puerto por defecto de postgreSQL.

Para la **persistencia**, he creado un volumen `pgdata`, en el directorio `/var/lib/postgresql/data` del contenedor. De esta forma, al destruir y volver a levantar un contenedor, los datos de la base de datos se conservarán.

#### Servicio de Backend
```yml
  backend:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: playtracker-backend
    restart: always
    depends_on:
      - db
    environment:
      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
    ports:
      - "8000:8000"
    command: >
      uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - ./:/app
```

Este servicio despliega el backend de la aplicación. La principal diferencia es que, en este caso, se crea desde cero, a diferencia del anterior que utilizaba una imagen oficial ya existente.

Debido a esto, es necesario un Dockerfile que especifique cómo instalar Python y las dependencias necesarias. La ruta del Dockerfile se especifica con `build:`, en lugar de `image`, que se utiliza para descargar una imagen prefabricada.

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir watchfiles

COPY . .
```

**FROM** especifica la base del contenedor, que en este caso es python. He utilizado la versión slim, porque es mucho más ligera al omitir librerías gráficas que no utilizaré.

**WORKDIR** especifica la ruta base de la aplicación. Cualquier comando a partir de aquí se hará en esa ruta.

**COPY** copia las dependencias del host a la ruta base de la aplicación en el contenedor.

**RUN** ejecuta comandos, en este caso estoy instalando las dependencias necesarias para el proyecto.

**COPY . .** copia todo el proyecto al contenedor.

> Se copian antes las dependencias por una razón. Si no cambia el `requirements.txt`, docker NO copia el nuevo y NO ejecuta el comando de instalación de dependencias, porque reconoce que ya lo ha hecho. De esta forma, si cambio el código pero no las dependencias, no se vuelven a instalar al levantar de nuevo el contenedor.

Sigamos con el `docker-compose.yml`. Las directivas nuevas que no se utilizaron para el servicio de base de datos son:
- `depends_on`: indica que depende del otro servicio, haciendo que espere a que arranque el otro para levantar este.
- `command`: ejecuta el comando que ejecuta el backend.

Por lo demás, no veo conveniente reiterar en las mismas directivas.

## Estructura del clúster de contenedores de tests
Esto ya se explicó en el [hito 2](../hito2/README.md), pero volveré a explicar en este las principales diferencias con el entorno de contenedores de desarrollo ya descrito en el anterior epígrafe.

Para la ejecución de los tests, se utiliza este otro compose, `docker-compose.test.yml`:
```yml
services:
  db_test:
    image: postgres:15
    container_name: playtracker-db-test
    env_file: .env.test
    restart: unless-stopped
    environment:
      POSTGRES_USER: playtracker
      POSTGRES_PASSWORD: playtracker
      POSTGRES_DB: playtracker_test
      PGDATA: /var/lib/postgresql/data/pgdata
    ports:
      - "5433:5432"
    tmpfs: 
      - /var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U playtracker -d playtracker_test"]
      interval: 5s
      timeout: 5s
      retries: 5
      start_period: 30s

  tests:
    build: .
    container_name: playtracker-tests
    env_file: .env.test
    depends_on:
      db_test:
        condition: service_healthy
    volumes:
      - ./:/app
    command: >
      sh -c "pytest --maxfail=1 --disable-warnings -v"
```

Las principales diferencias con el docker-compose descrito anteriormente son las siguientes:
- Uso de memoria RAM para montar la base de datos (`tmpfs`). No necesitamos persistencia en los tests ya que es una ejecución aislada.
- Cambio de puertos para no generar conflictos con el otro entorno.
- Uso de **healthcheck** para garantizar que la base de datos esté lista antes de ejecutar los tests.
- El comando de ejecución ahora es `  sh -c "pytest --maxfail=1 --disable-warnings -v"`, que ejecuta los tests y muere inmediatamente después.
- Uso de las variables de entorno de `env.test`, en lugar de las de .env. Como no es el archivo de entorno por defecto, hay que especificarlo con `env_file`.
