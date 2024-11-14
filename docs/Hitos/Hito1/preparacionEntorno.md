# PlayTracker - Preparación inicial del entorno y control de versiones

## Configuración de la cuenta
Para más seguridad, he activado la verificación en dos pasos de GitHub, utilizando el autenticador de Google.

## Creación y configuración del respositorio
Al ser un proyecto nuevo, he tenido que crear y configurar un nuevo repositorio de GitHub y enlazarlo con un repositorio local.
Para ello, he creado primero un nuevo repositorio en GitHub con el nombre de la aplicación.

Después, cloné en mi ordenador el repositorio:
   ```bash
   git clone https://github.com/Antongd111/PlayTracker.git
   ```

Y desde ahí, creé los archivos de licencia, README y el fichero para el hito 1.
Los primeros commits los he hecho directamente en la rama máster, dado que eran solo cambios en los archivos de documentación. Sin embargo, es una buena práctica trabajar en diferentes ramas una vez comience con el desarrollo.

## Creación del entorno de frontend
Para el frontend, utilizaré expo. Expo es un framework de React Native que ofrece herramientas como bibliotecas de desarrollo y utilidades como la capacidad de ejecutar la aplicación directamente en el dispositivo móvil en tiempo de desarrollo sin necesidad de compilarla. Para crear un proyecto de Expo, se instala y se ejecuta este el comando **expo init**:

   ```bash
   expo init play-tracker
   ```

Y se crea una carpeta con los archivos iniciales del código fuente. Tras reorganizarlo un poco para tener la documentación de los hitos por un lado y el código por otro, ha quedado así:

[Estructura creada](../../Images/EntornoCreado.png)

Teniendo ya el frontend creado, vamos con el backend.