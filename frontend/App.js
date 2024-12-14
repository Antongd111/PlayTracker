import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import AppStackNavigator from './navigation/AppStackNavigator';
import { ActivityIndicator, View, StyleSheet } from 'react-native';
import { useFonts, Audiowide_400Regular } from '@expo-google-fonts/audiowide';

export default function App() {
  const [fontsLoaded] = useFonts({
    Audiowide_400Regular,
  });

  if (!fontsLoaded) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#00D9FF" />
      </View>
    );
  }

  return (
    <NavigationContainer>
      <AppStackNavigator />
    </NavigationContainer>
  );
}

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#16213E',
  },
});
