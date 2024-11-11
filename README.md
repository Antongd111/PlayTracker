# Gestión de Videojuegos - Seguimiento y Opiniones

## Descripción del Proyecto

Esta aplicación permite a los usuarios hacer un seguimiento de los videojuegos que están jugando, han completado o planean jugar, organizándolos en bibliotecas personalizadas. Además, los usuarios pueden añadir opiniones y calificaciones a cada videojuego, facilitando la gestión y el registro de su experiencia en el mundo de los videojuegos, y compartiendo sus opiniones con otros usuarios.

### Características principales

- **Bibliotecas de videojuegos**: Los usuarios pueden organizar sus videojuegos en distintas bibliotecas (ej.: Completados, En Progreso, Pendientes).
- **Opiniones y calificaciones**: Posibilidad de agregar opiniones, comentarios y calificar cada videojuego.
- **API de RAWG**: La aplicación utiliza la API de RAWG para obtener información detallada de cada videojuego, como descripciones, géneros, y capturas de pantalla.
- **Gestión de usuarios y almacenamiento**: Firebase es utilizado para el backend de la aplicación, proporcionando autenticación de usuarios y almacenamiento de datos en la nube para que cada usuario tenga acceso a sus bibliotecas y opiniones de forma personalizada.
- **Recomendación de juegos**: Posibilidad de recomendar videojuegos a usuarios añadidos como amigos.

---

## Tecnologías Utilizadas

La aplicación está desarrollada utilizando las siguientes tecnologías:

- **Frontend**: **React Native** para crear una aplicación móvil multiplataforma que funcione tanto en Android como en iOS.
- **API de Videojuegos**: La aplicación se conecta a la API de **RAWG** para obtener información sobre videojuegos en tiempo real.
- **Backend**: **Node.js** y **Express** para gestionar la lógica de negocio y la creación de una API REST que maneje las operaciones de usuarios, videojuegos y opiniones.
- **Despliegue en la nube**: El backend será desplegado en la nube permitiendo accesibilidad y escalabilidad de la aplicación.
- **Control de versiones**: `git` para el control de versiones y **GitHub** como repositorio para almacenar el código y la documentación.

---

## Instalación

Para ejecutar esta aplicación en un entorno local, sigue estos pasos **(la aplicación está en desarollo y la instalación es susceptible a cambios si decido modificar algo en la estructura en tecnologías)**:

1. **Clona el repositorio**:
   ```bash
   git clone https://github.com/Antongd111/AppJuegos-CC.git
   ```
   
2. **Navega al directorio del proyecto**:
   ```bash
   cd AppJuegos-CC
   ```

3. **Instala las dependencias**:
   ```bash
   npm install
   ```
   
4. **Configura las variables de entorno**:
   Es necesaria una clave de la api de RAWG para el acceso. Inclúyela en rawgApiConfig.js.

5. **Inicia el frontend**:
   ```bash
   npx react-native run-android
   ```

5. **Inicia el backend**:
   ```bash
   cd backend
   npm start
   ```
