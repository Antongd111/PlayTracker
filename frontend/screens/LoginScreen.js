import React from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Alert } from 'react-native';
import { loginUser } from '../services/authService';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useNavigation } from '@react-navigation/native';
import {LinearGradient} from 'expo-linear-gradient';

const LoginScreen = () => {
  const [email, setEmail] = React.useState('');
  const [password, setPassword] = React.useState('');
  const navigation = useNavigation();

  const handleLogin = async () => {
    try {
      // Send login request to backend
      const { token, user } = await loginUser(email, password);

      // Save token in AsyncStorage
      await AsyncStorage.setItem('userToken', token);
      await AsyncStorage.setItem('user', JSON.stringify(user));

      navigation.replace('App');
    } catch (error) {
      console.error(error);
      Alert.alert('Login Failed', error.response?.data?.error || 'Something went wrong');
    }
  };

  return (
    <LinearGradient colors={['#0F3460', '#16213E']} style={styles.container}>
      <View style={styles.formContainer}>
        <Text style={styles.title}>Welcome back!</Text>
        <TextInput
          style={styles.input}
          placeholder="Email"
          placeholderTextColor="#00D9FF"
          onChangeText={setEmail}
        />
        <TextInput
          style={styles.input}
          placeholder="Password"
          placeholderTextColor="#00D9FF"
          onChangeText={setPassword}
          secureTextEntry
        />
        <TouchableOpacity style={styles.button} onPress={handleLogin}>
          <Text style={styles.buttonText}>LOGIN</Text>
        </TouchableOpacity>
      </View>
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    padding: 16,
  },
  formContainer: {
    backgroundColor: '#1A1A2E',
    borderRadius: 10,
    padding: 20,
    shadowColor: '#FFD700',
    shadowOpacity: 0.8,
    shadowRadius: 10,
    elevation: 20,
  },
  title: {
    fontSize: 28,
    color: '#FFD700',
    marginBottom: 20,
    textAlign: 'center',
    fontFamily: 'Audiowide_400Regular',
  },
  input: {
    height: 50,
    borderColor: '#00D9FF',
    borderWidth: 2,
    borderRadius: 8,
    marginBottom: 16,
    paddingHorizontal: 10,
    color: '#F6F5F1',
    backgroundColor: '#0F3460',
  },
  button: {
    backgroundColor: '#FFD700',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
    shadowColor: '#FFD700',
    shadowOpacity: 1,
    shadowRadius: 15,
    elevation: 5,
  },
  buttonText: {
    color: '#13100F',
    fontSize: 18,
    fontFamily: 'Audiowide_400Regular',
  },
});

export default LoginScreen;