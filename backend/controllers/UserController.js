const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
const User = require('../models/User');

exports.register = async (req, res) => {
  const { username, email, password } = req.body;

  try {
    const hashedPassword = await bcrypt.hash(password, 10);

    const user = await User.create({
      username,
      email,
      password: hashedPassword,
    });

    res.status(201).json({ message: 'User registered successfully', user });
  } catch (error) {
    res.status(400).json({ message: 'Error registering user', error });
  }
};

exports.login = async (req, res) => {
    const { email, password } = req.body;
    
    try {
        
      const user = await User.findOne({ where: { email } });

      if (!user) {
        return res.status(404).json({ message: 'User not found' });
      }

      const isMatch = await bcrypt.compare(password, user.password);
      if (!isMatch) {
        return res.status(401).json({ message: 'Invalid credentials' });
      }
      
      const token = jwt.sign(
        { id: user.id, username: user.username },
        process.env.JWT_SECRET,
        { expiresIn: '1d' }
      );
  
      res.status(200).json({ message: 'Login successful', token });
    } catch (error) {
      console.log(error);
      res.status(500).json({ message: 'Error logging in', error });
    }
  };

  exports.getUserProfile = async (req, res) => {
    try {
      const user = req.user;
      res.status(200).json({
        id: user.id,
        username: user.username,
        email: user.email,
      });
    } catch (error) {
      res.status(500).json({ message: 'Error fetching user profile', error });
    }
  };

// Ruta protegida
exports.protectedRoute = (req, res) => {
    res.status(200).json({ message: 'Accessed protected route', user: req.user });
  };