const express = require('express');
const userRoutes = require('./routes/UserRoutes');
const rawgRoutes = require('./routes/rawgRoutes');
require('dotenv').config();

const app = express();

// Middlewares
app.use(express.json());

// Routes
app.use('/api/users', userRoutes);
app.use('/api/rawg', rawgRoutes);

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});