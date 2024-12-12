import React, { useState } from 'react';
import { View, Text, StyleSheet, ActivityIndicator, TextInput, Button, FlatList } from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import api from '../services/api';

export default function ExploreScreen() {
  const [query, setQuery] = useState('');
  const [games, setGames] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    setLoading(true);
    try {
      const response = await api.get('/rawg/games', { params: { query } });
      setGames(response.data.results);
    } catch (error) {
      console.error('Error searching games:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Explore Screen</Text>
      <Text style={styles.subtitle}>Discover new content here!</Text>

      <View style={styles.iconContainer}>
        <Icon name="location-outline" size={30} color="#6A5ACD" />
        <Icon name="bookmark-outline" size={30} color="#6A5ACD" />
        <Icon name="notifications-outline" size={30} color="#6A5ACD" />
      </View>

      <TextInput
        style={styles.input}
        placeholder="Search games..."
        value={query}
        onChangeText={setQuery}
      />
      <Button title="Search" onPress={handleSearch} />

      {loading ? (
        <ActivityIndicator size="large" color="#6A5ACD" />
      ) : (
        <FlatList
          data={games}
          keyExtractor={(item) => item.id.toString()}
          renderItem={({ item }) => (
            <Text style={styles.gameItem}>{item.name}</Text>
          )}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 10,
  },
  subtitle: {
    fontSize: 18,
    color: 'gray',
    marginBottom: 20,
  },
  iconContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    width: '60%',
    marginVertical: 20,
  },
  input: {
    width: '80%',
    borderWidth: 1,
    borderColor: '#ccc',
    padding: 10,
    borderRadius: 5,
    marginVertical: 10,
  },
  gameItem: {
    padding: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#ccc',
  },
});