import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import AppStackNavigator from './navigation/AppStackNavigator';

export default function App() {
  return (
    <NavigationContainer>
      <AppStackNavigator />
    </NavigationContainer>
  );
}