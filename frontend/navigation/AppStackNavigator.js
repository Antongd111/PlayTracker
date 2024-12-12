import React from 'react';
import { createStackNavigator } from '@react-navigation/stack';
import LoginScreen from '../screens/LoginScreen';
import AppNavigator from './AppNavigator'; // Importa el Tab Navigator

const Stack = createStackNavigator();

function AppStackNavigator() {
  return (
    <Stack.Navigator initialRouteName="Login">
      <Stack.Screen
        name="Login"
        component={LoginScreen}
        options={{ headerShown: false }} // Oculta el header en la pantalla de Login
      />
      <Stack.Screen
        name="App"
        component={AppNavigator}
        options={{ headerShown: false }} // Oculta el header en el Tab Navigator
      />
    </Stack.Navigator>
  );
}

export default AppStackNavigator;