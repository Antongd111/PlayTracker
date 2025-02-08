import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ActivityIndicator, TextInput, TouchableOpacity, FlatList, Image } from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import { searchGames, getUserGames } from '../services/gamesService';
import StarRating from '../components/StarRating';
import AsyncStorage from '@react-native-async-storage/async-storage';
import GameInfoModal from '../components/GameInfoModal';
import { updateGameStatus } from '../services/gamesService';

export default function ExploreScreen() {
  const [query, setQuery] = useState('');
  const [games, setGames] = useState([]);
  const [userGames, setUserGames] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedGame, setSelectedGame] = useState(null);
  const [modalVisible, setModalVisible] = useState(false);

  // Get user games on component mount
  useEffect(() => {
    const fetchUserGames = async () => {
      try {
        const userId = JSON.parse(await AsyncStorage.getItem('user')).id;
        const response = await getUserGames(userId);

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

  const getGameStatus = (gameId) => {
    const userGame = userGames.find((ug) => ug.rawgGameId === gameId);
    return userGame ? userGame.status : null;
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'Completed':
        return <Icon name="checkmark-circle" size={25} color="#39FF14" />;
      case 'Playing':
        return <Icon name="play-circle" size={25} color="#FFD700" />;
      case 'Saved':
        return <Icon name="bookmark" size={25} color="#E94560" />;
      default:
        return <Icon name="bookmark-outline" size={25} color="#E94560" />;
    }
  };

  const updateStatus = async (game) => {
    const userGame = userGames.find((ug) => ug.rawgGameId === game.id);
    const userData = await AsyncStorage.getItem('user');
    const userId = JSON.parse(userData).id;
  
    let newStatus;
    console.log('Current game status:', userGame?.status);
  
    switch (userGame?.status) {
      case 'Completed':
        newStatus = 'notSaved';
        break;
      case 'Playing':
        newStatus = 'Completed';
        break;
      case 'Saved':
        newStatus = 'Playing';
        break;
      default:
        newStatus = 'Saved';
        break;
    }
  
    // Actualizar estado local antes de la llamada al backend
    setUserGames((prevUserGames) =>
      prevUserGames.map((g) =>
        g.rawgGameId === game.id ? { ...g, status: newStatus } : g
      )
    );
  
    console.log('Updating game status:', game.id, newStatus);
  
    try {
      await updateGameStatus(userId, game.id, newStatus);
    } catch (error) {
      console.error('Error updating game status:', error);
  
      // Revertir cambios locales si el backend falla
      setUserGames((prevUserGames) =>
        prevUserGames.map((g) =>
          g.rawgGameId === game.id ? { ...g, status: userGame?.status } : g
        )
      );
    }
  };

  const openModal = (game) => {
    const formattedGame = {

      id: game.id,
      title: game.name,
      status: getGameStatus(game.id),
      rawgGameId: game.id,
      rawgDetails: {
        background_image: game.background_image || '',
        name: game.name,
        released: game.released || 'Unknown',
        rating: game.rating || 'N/A',
        description_raw: game.description_raw || 'No description available',
      }
    };
  
    setSelectedGame(formattedGame);
    setModalVisible(true);
  };

  const closeModal = () => {
    setSelectedGame(null);
    setModalVisible(false);
  };

  const renderGameItem = ({ item }) => {
    const status = getGameStatus(item.id);

    return (
      <TouchableOpacity onPress={() => openModal(item)}>
        <View style={styles.gameCard}>
          <Image source={{ uri: item.background_image }} style={styles.gameImage} />
          <View style={styles.gameDetails}>
            <Text style={styles.gameTitle}>{item.name}</Text>
            <Text style={styles.gameDate}>{new Date(item.released).getFullYear()}</Text>
            <StarRating rating={item.rating} />
          </View>
          <TouchableOpacity style={styles.statusIcon} onPress={() => updateStatus(item)}>{getStatusIcon(status)}</TouchableOpacity>
        </View>
      </TouchableOpacity>
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

      <GameInfoModal visible={modalVisible} onClose={closeModal} game={selectedGame} />
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
    padding: 10,
    alignItems: 'center',
    position: 'relative',
    elevation: 7,
    shadowColor: '#FFD700',
    shadowOpacity: 0.8,
    shadowRadius: 10,
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
