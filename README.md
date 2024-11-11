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
- **Backend en la Nube**: **Firebase** se utiliza para gestionar el almacenamiento de datos (bibliotecas y opiniones), así como para la autenticación de usuarios.
- **Despliegue en la nube**: Firebase también facilita el despliegue y la sincronización en tiempo real, permitiendo una experiencia fluida de usuario.
- **Control de versiones**: `git` para el control de versiones y **GitHub** como repositorio para almacenar el código y la documentación.

---
