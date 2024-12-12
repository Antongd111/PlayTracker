import React, { useEffect, useState } from 'react';
import { View, Text, Button, StyleSheet, ActivityIndicator } from 'react-native';
import api from '../services/api';

export default function HomeScreen({ navigation }) {
  const [loading, setLoading] = useState(false);

  const handleFetchGames = async () => {
    setLoading(true);
    try {
      const response = await api.get('/rawg/games', {
        params: { query: 'zelda', page: 1 },
      });
      console.log('Fetched games:', response.data.results);
    } catch (error) {
      console.error('Error fetching games:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.text}>Welcome to the Home Screen!</Text>
      {loading ? (
        <ActivityIndicator size="large" color="#6A5ACD" />
      ) : (
        <Button title="Go to Game Details" onPress={() => navigation.navigate('GameDetails')} />
      )}
      <Button title="Fetch Games" onPress={handleFetchGames} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  text: {
    fontSize: 20,
    marginBottom: 20,
  },
});