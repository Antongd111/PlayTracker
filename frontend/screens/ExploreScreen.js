import React, { useState } from 'react';
import { View, Text, StyleSheet, ActivityIndicator, TextInput, TouchableOpacity, FlatList, Image } from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import { searchGames } from '../services/gamesService';

export default function ExploreScreen() {
  const [query, setQuery] = useState('');
  const [games, setGames] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const response = await searchGames(query);
      setGames(response.results);
    } catch (error) {
      console.error('Error searching games:', error);
    } finally {
      setLoading(false);
    }
  };

  const renderGameItem = ({ item }) => (
    <View style={styles.gameCard}>
      <Image source={{ uri: item.background_image }} style={styles.gameImage} />
      <View style={styles.gameDetails}>
        <Text style={styles.gameTitle}>{item.name}</Text>
        <Text style={styles.gameDate}>{item.released}</Text>
        <Text style={styles.gameRating}>Rating: {item.rating}</Text>
      </View>
    </View>
  );

  return (
    <View style={styles.container}>
      <View style={styles.searchContainer}>
        <TextInput
          style={styles.input}
          placeholder="Search games..."
          placeholderTextColor="#A0A0A0"
          value={query}
          onChangeText={setQuery}
        />
        <TouchableOpacity onPress={handleSearch} style={styles.searchButton}>
          <Icon name="search" size={24} color="#FFD700" />
        </TouchableOpacity>
      </View>

      {loading ? (
        <ActivityIndicator size="large" color="#FFD700" />
      ) : (
        <FlatList
          data={games}
          keyExtractor={(item) => item.id.toString()}
          renderItem={renderGameItem}
          contentContainerStyle={styles.gamesList}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1A1A2E',
    padding: 10,
  },
  searchContainer: {
    flexDirection: 'row',
    marginBottom: 10,
  },
  input: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#FFD700',
    borderRadius: 10,
    padding: 10,
    backgroundColor: '#0F3460',
    color: '#FFFFFF',
  },
  searchButton: {
    marginLeft: 10,
    backgroundColor: '#13100F',
    padding: 10,
    borderRadius: 10,
    borderColor: '#FFD700',
    borderWidth: 2,
  },
  gamesList: {
    paddingBottom: 20,
  },
  gameCard: {
    flexDirection: 'row',
    backgroundColor: '#0F3460',
    borderRadius: 10,
    marginVertical: 5,
    borderWidth: 2,
    borderColor: '#FFD700',
    shadowColor: '#FFD700',
    shadowOpacity: 0.8,
    shadowRadius: 10,
    padding: 10,
    alignItems: 'center',
  },
  gameImage: {
    width: 100,
    height: 60,
    borderRadius: 8,
    marginRight: 10,
  },
  gameDetails: {
    flex: 1,
    justifyContent: 'center',
  },
  gameTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#FFD700',
  },
  gameDate: {
    fontSize: 14,
    color: '#A0A0A0',
  },
  gameRating: {
    fontSize: 14,
    color: '#39FF14',
  },
});
