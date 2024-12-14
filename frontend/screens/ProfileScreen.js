import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, Image, FlatList, ActivityIndicator, TouchableOpacity } from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { getUserGames } from '../services/gamesService';

export default function ProfileScreen() {
  const insets = useSafeAreaInsets();

  // User data
  const [username, setUsername] = useState('');
  const [status, setStatus] = useState('');
  const [loading, setLoading] = useState(true);
  const [games, setGames] = useState([]);
  const [filter, setFilter] = useState('all');

  const formatUserGames = (gamesData) => {
    return gamesData.games.map(game => ({
      id: game.id,
      title: game.title,
      status: game.status,
      rawgGameId: game.rawgGameId,
      userId: game.userId,
      rawgDetails: {
        ...game.rawgDetails
      }
    }));
  };

  /**
   * Load user data from AsyncStorage
   */
  const loadUserData = async () => {
    try {
      const userData = await AsyncStorage.getItem('user');

      if (userData) {
        const { username, statusMessage } = JSON.parse(userData);
        setUsername(username);
        setStatus(statusMessage || '');
      }
    } catch (error) {
      console.error('Error loading user data:', error);
    }
  };

  /**
   * Load user games from the backend
   */
  const loadUserGames = async () => {
    try {
      const userId = JSON.parse(await AsyncStorage.getItem('user')).id;

      const games = await getUserGames(userId);

      if (games) {
        const formattedGames = formatUserGames(games);
        console.log('Formatted Games:', formattedGames);
        setGames(formattedGames);
      }

    } catch (error) {
      console.error('Error loading user games:', error);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Filter the games based on the selected filter
  */
  const filteredGames = filter === 'All' ? games : games.filter(game => game.status === filter);

  const getCardStyle = (status) => {
    switch (status) {
      case 'Completed':
        return { backgroundColor: '#d4edda', borderColor: '#28a745' }; // Verde
      case 'Playing':
        return { backgroundColor: '#fff3cd', borderColor: '#ffc107' }; // Amarillo
      case 'Saved':
        return { backgroundColor: '#f8d7da', borderColor: '#dc3545' }; // Rojo
      default:
        return { backgroundColor: '#e8e8e8', borderColor: '#ccc' };    // Por defecto
    }
  };

  const getButtonStyle = (currentFilter, buttonFilter) => {
    if (currentFilter === buttonFilter) {
      switch (buttonFilter) {
        case 'All':
          return [styles.allFilter, { backgroundColor: '#9989ff', borderColor: '#6A5ACD' }];
        case 'Completed':
          return [styles.option, { backgroundColor: '#7bfb80', borderColor: '#4CAF50' }];
        case 'Playing':
          return [styles.option, { backgroundColor: '#fad76f', borderColor: '#FFC107' }];
        case 'Saved':
          return [styles.option, { backgroundColor: '#fe746a', borderColor: '#F44336' }];
        default:
          return styles.option;
      }
    }
    return buttonFilter === 'All' ? styles.allFilter : styles.option;
  };
  
  const getButtonTextStyle = (currentFilter, buttonFilter) => {
    return currentFilter === buttonFilter ? { color: '#fff' } : { color: '#333' };
  };

  useEffect(() => {
    loadUserData();
    loadUserGames();
  }, []);

  /**
   * Render each game card
   */
  const renderGameItem = ({ item }) => (
    <View style={[styles.gameCard, getCardStyle(item.status)]}>
      <Image source={{ uri: item.rawgDetails.background_image }} style={styles.gameImage} />
      <Text style={styles.gameTitle}>{item.rawgDetails.name}</Text>
      <Text style={styles.gameDate}>{new Date(item.rawgDetails.released).getFullYear()}</Text>
      <Text style={styles.gameRating}>Rating: {item.rawgDetails.rating}</Text>
    </View>
  );

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <View style={styles.profileHeader}>
        <View style={styles.profileIconContainer}>
          <Icon name="person-circle-outline" size={100} color="#6A5ACD" />
        </View>
        <View style={styles.profileText}>
          <Text style={styles.username}>{username}</Text>
          <Text style={styles.status}>{status}</Text>
        </View>
      </View>

      {/* Menu de filtros */}
      <View style={styles.filtersLargeContainer}>
        <TouchableOpacity style={getButtonStyle(filter, 'All')} onPress={() => setFilter('All')}>
          <Icon name="list-outline" size={25} color={filter === 'All' ? '#fff' : '#6A5ACD'} />
          <Text style={getButtonTextStyle(filter, 'All')}>All</Text>
        </TouchableOpacity>

        <View style={styles.filtersSmallContainer}>
          <TouchableOpacity style={getButtonStyle(filter, 'Completed')} onPress={() => setFilter('Completed')}>
            <Icon name="checkmark-done-outline" size={25} color={filter === 'Completed' ? '#fff' : '#6A5ACD'} />
            <Text style={getButtonTextStyle(filter, 'Completed')}>Completed</Text>
          </TouchableOpacity>

          <TouchableOpacity style={getButtonStyle(filter, 'Playing')} onPress={() => setFilter('Playing')}>
            <Icon name="pulse-outline" size={25} color={filter === 'Playing' ? '#fff' : '#6A5ACD'} />
            <Text style={getButtonTextStyle(filter, 'Playing')}>Playing</Text>
          </TouchableOpacity>

          <TouchableOpacity style={getButtonStyle(filter, 'Saved')} onPress={() => setFilter('Saved')}>
            <Icon name="receipt-outline" size={25} color={filter === 'Saved' ? '#fff' : '#6A5ACD'} />
            <Text style={getButtonTextStyle(filter, 'Saved')}>Saved</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Lista de juegos filtrada */}
      <FlatList
        data={filteredGames}
        keyExtractor={(item) => item.id.toString()}
        renderItem={renderGameItem}
        numColumns={3}
        contentContainerStyle={styles.gamesList}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  profileHeader: {
    paddingBottom: '5%',
    paddingTop: '5%',
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#cfcfcf',
  },
  profileIconContainer: {
    marginLeft: '5%',
    marginRight: '3%',
  },
  profileText: {
    flexDirection: 'column',
  },
  username: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 5,
  },
  status: {
    fontSize: 16,
    color: 'gray',
  },

  filtersSmallContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    backgroundColor: '#cfcfcf',
    padding: '3%',
  },
  filtersLargeContainer: {
    flexDirection: 'column',
    justifyContent: 'space-around',
    backgroundColor: '#cfcfcf',
    padding: '3%',
  },
  option: {
    alignItems: 'center',
    borderWidth: 1,
    width: '30%',
    padding: '2%',
    borderRadius: 5,
    borderColor: '#6A5ACD',
    backgroundColor: 'white',
  },
  allFilter: {
    alignItems: 'center',
    alignSelf: 'center',
    borderWidth: 1,
    width: '90%',
    padding: '2%',
    borderRadius: 5,
    borderColor: '#6A5ACD',
    backgroundColor: 'white',
  },
  optionText: {
    marginTop: 5,
    fontSize: 14,
    color: '#333',
  },

  loadingIndicator: {
    marginTop: 20,
  },
  gamesList: {
    paddingHorizontal: 5,
    paddingBottom: 20,
  },
  gameCard: {
    width: '30%',
    padding: 10,
    margin: 5,
    backgroundColor: '#e8e8e8',
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  gameImage: {
    width: '100%',
    height: 80,
    borderRadius: 8,
    marginBottom: 5,
  },
  gameTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 5,
  },
  gameDate: {
    fontSize: 12,
    color: '#333',
    textAlign: 'center',
  },
  gameRating: {
    fontSize: 12,
    color: '#888',
    textAlign: 'center',
  },
  gameStatus: {
    fontSize: 12,
    color: '#444',
    textAlign: 'center',
  },
});
