import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ActivityIndicator, TextInput, TouchableOpacity, FlatList, Image } from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import { searchGames, getUserGames } from '../services/gamesService';
import StarRating from '../components/StarRating';
import AsyncStorage from '@react-native-async-storage/async-storage';

export default function ExploreScreen() {
  const [query, setQuery] = useState('');
  const [games, setGames] = useState([]);
  const [userGames, setUserGames] = useState([]);
  const [loading, setLoading] = useState(false);

  // Get user games on component mount
  useEffect(() => {
    const fetchUserGames = async () => {
      try {
        const userId = JSON.parse(await AsyncStorage.getItem('user')).id;
        const response = await getUserGames(userId);
    
        // Extraemos la propiedad games
        if (response && Array.isArray(response.games)) {
          setUserGames(response.games);
        } else {
          console.error('userGames no es un array:', response);
          setUserGames([]);
        }
      } catch (error) {
        console.error('Error fetching user games:', error);
        setUserGames([]);
      }
    };

    fetchUserGames();
  }, []);

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

  // Function that returns the status of a game
  const getGameStatus = (gameId) => {
    const userGame = userGames.find((ug) => ug.rawgGameId === gameId);
    return userGame ? userGame.status : null;
  };

  // Function that returns the icon for the status of a game
  const getStatusIcon = (status) => {
    switch (status) {
      case 'Completed':
        return <Icon name="checkmark-circle" size={20} color="#39FF14" />;
      case 'Playing':
        return <Icon name="play-circle" size={20} color="#FFD700" />;
      case 'Saved':
        return <Icon name="bookmark" size={20} color="#E94560" />;
      default:
        return null;
    }
  };

  const renderGameItem = ({ item }) => {
    const status = getGameStatus(item.id);
    return (
      <View style={styles.gameCard}>
        <Image source={{ uri: item.background_image }} style={styles.gameImage} />
        <View style={styles.gameDetails}>
          <Text style={styles.gameTitle}>{item.name}</Text>
          <Text style={styles.gameDate}>{new Date(item.released).getFullYear()}</Text>
          <StarRating rating={item.rating} />
        </View>
        <View style={styles.statusIcon}>
          {getStatusIcon(status)}
        </View>
      </View>
    );
  };

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
    backgroundColor: '#16213E',
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
    position: 'relative',
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
  statusIcon: {
    position: 'absolute',
    top: 10,
    right: 10,
  },
});
