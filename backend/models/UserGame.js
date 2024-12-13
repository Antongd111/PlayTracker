const { DataTypes } = require('sequelize');
const sequelize = require('../config/database');
const User = require('./User');

const UserGame = sequelize.define('UserGame', {
  rawgGameId: {
    type: DataTypes.INTEGER,
    allowNull: false,
  },
  title: {
    type: DataTypes.STRING,
    allowNull: false,
  },
  status: {
    type: DataTypes.ENUM('Completed', 'Playing', 'Saved'),
    allowNull: false,
  },
}, {
  tableName: 'usergame',
  freezeTableName: true,
  timestamps: false,
});

// Relaciones
User.hasMany(UserGame, { foreignKey: 'userId', onDelete: 'CASCADE' });
UserGame.belongsTo(User, { foreignKey: 'userId' });

module.exports = UserGame;