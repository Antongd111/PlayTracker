const express = require('express');
const userRoutes = require('./routes/UserRoutes'); // Importar las rutas de usuarios
require('dotenv').config(); // Leer variables de entorno

const app = express();

// Middlewares
app.use(express.json()); // Para manejar datos JSON en las solicitudes

// Rutas
app.use('/api/users', userRoutes); // Registrar las rutas de usuario

// Configurar el puerto
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});