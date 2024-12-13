const express = require('express');
const userRoutes = require('./routes/UserRoutes');
const rawgRoutes = require('./routes/rawgRoutes');
require('dotenv').config();
const sequelize = require('./config/database');
const User = require('./models/User');
const UserGame = require('./models/UserGame');

const app = express();

// Middlewares
app.use(express.json());

// Routes
app.use('/api/users', userRoutes);
app.use('/api/rawg', rawgRoutes);

// Sync database
(async () => {
  try {
    await sequelize.sync({ alter: true });
    console.log('Database synced successfully.');
  } catch (error) {
    console.error('Error syncing database:', error);
  }
})();

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});