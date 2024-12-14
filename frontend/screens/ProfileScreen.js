import React, { useEffect, useState, useRef } from 'react';
import { View, Text, StyleSheet, Image, FlatList, ActivityIndicator, TouchableOpacity, Animated } from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { getUserGames } from '../services/gamesService';
import { LinearGradient } from 'expo-linear-gradient';

export default function ProfileScreen() {
  const insets = useSafeAreaInsets();

  const [username, setUsername] = useState('');
  const [status, setStatus] = useState('');
  const [loading, setLoading] = useState(true);
  const [games, setGames] = useState([]);
  const [filter, setFilter] = useState('All');

  const scaleAnim = useRef(new Animated.Value(1)).current;

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

  const loadUserGames = async () => {
    try {
      const userId = JSON.parse(await AsyncStorage.getItem('user')).id;
      const games = await getUserGames(userId);
      if (games) {
        setGames(formatUserGames(games));
      }
    } catch (error) {
      console.error('Error loading user games:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredGames = filter === 'All' ? games : games.filter(game => game.status === filter);

  const handleFilterPress = (selectedFilter) => {
    setFilter(selectedFilter);

    // Trigger scale animation
    scaleAnim.setValue(1);
    Animated.sequence([
      Animated.timing(scaleAnim, {
        toValue: 1.1,
        duration: 100,
        useNativeDriver: true,
      }),
      Animated.timing(scaleAnim, {
        toValue: 1,
        duration: 100,
        useNativeDriver: true,
      }),
    ]).start();
  };

  const getCardStyle = (status) => {
    switch (status) {
      case 'Completed':
        return { borderColor: '#39FF14' }; // Verde neón
      case 'Playing':
        return { borderColor: '#FFD700' }; // Amarillo neón
      case 'Saved':
        return { borderColor: '#E94560' }; // Rojo neón
      default:
        return { borderColor: '#16213E' }; // Gris oscuro por defecto
    }
  };

  useEffect(() => {
    loadUserData();
    loadUserGames();
  }, []);

  const renderGameItem = ({ item }) => (
    <View style={[styles.gameCard, getCardStyle(item.status)]}>
      <Image source={{ uri: item.rawgDetails.background_image }} style={styles.gameImage} />
      <View style={styles.gameInfo}>
        <Text style={styles.gameTitle}>{item.rawgDetails.name}</Text>
        <Text style={styles.gameDate}>{new Date(item.rawgDetails.released).getFullYear()}</Text>
      </View>
    </View>
  );
  
  return (
    <View style={[styles.container]}>
      <View style={styles.profileHeader}>
        <Icon name="person-circle-outline" size={100} color="#00D9FF" />
        <View style={styles.profileText}>
          <Text style={styles.username}>{username}</Text>
          <Text style={styles.status}>{status}</Text>
        </View>
      </View>
  
      <LinearGradient colors={['#16213E', '#3b5998']} style={styles.filtersContainer}>
        <TouchableOpacity onPress={() => handleFilterPress('All')}>
          <Animated.View style={[styles.option, filter === 'All' && styles.activeOption]}>
            <Icon name="list-outline" size={25} color={filter === 'All' ? '#FFD700' : '#00D9FF'} />
            <Text style={styles.optionText}>All</Text>
          </Animated.View>
        </TouchableOpacity>
  
        <TouchableOpacity onPress={() => handleFilterPress('Completed')}>
          <Animated.View style={[styles.option, filter === 'Completed' && styles.activeOption]}>
            <Icon name="checkmark-done-outline" size={25} color={filter === 'Completed' ? '#FFD700' : '#00D9FF'} />
            <Text style={styles.optionText}>Completed</Text>
          </Animated.View>
        </TouchableOpacity>
  
        <TouchableOpacity onPress={() => handleFilterPress('Playing')}>
          <Animated.View style={[styles.option, filter === 'Playing' && styles.activeOption]}>
            <Icon name="pulse-outline" size={25} color={filter === 'Playing' ? '#FFD700' : '#00D9FF'} />
            <Text style={styles.optionText}>Playing</Text>
          </Animated.View>
        </TouchableOpacity>
  
        <TouchableOpacity onPress={() => handleFilterPress('Saved')}>
          <Animated.View style={[styles.option, filter === 'Saved' && styles.activeOption]}>
            <Icon name="receipt-outline" size={25} color={filter === 'Saved' ? '#FFD700' : '#00D9FF'} />
            <Text style={styles.optionText}>Saved</Text>
          </Animated.View>
        </TouchableOpacity>
      </LinearGradient>
  
      {loading ? (
        <ActivityIndicator size="large" color="#00D9FF" />
      ) : (
        <FlatList
          data={filteredGames}
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
  },
  profileHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#16213E',
  },
  profileText: {
    marginLeft: 15,
  },
  username: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#00D9FF',
  },
  status: {
    fontSize: 16,
    color: '#E94560',
  },
  filtersContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    backgroundColor: '#0F3460',
    paddingVertical: 10,
  },
  option: {
    alignItems: 'center',
    padding: 12,
    borderWidth: 2,
    borderColor: '#00D9FF',
    borderRadius: 10,
    backgroundColor: '#1A1A2E',
    shadowRadius: 16,
  },
  activeOption: {
    backgroundColor: '#13100F',
    borderColor: '#FFD700',
    shadowColor: '#FFD700',
    shadowOpacity: 0.8,
    shadowRadius: 10,
    elevation: 40,
    shadowOffset: { width: 0, height: 0 },
    borderWidth: 2,
  },
  optionText: {
    marginTop: 5,
    color: '#00D9FF',
    fontSize: 14,
  },
  gamesList: {
    padding: 10,
  },
  gameCard: {
    flexDirection: 'row',
    padding: 10,
    marginBottom: 10,
    borderRadius: 8,
    borderWidth: 1,
    alignItems: 'center',
  },
  gameImage: {
    width: 100,
    height: 80,
    borderRadius: 8,
    marginRight: 15,
  },
  gameInfo: {
    flex: 1,
    justifyContent: 'center',
  },
  gameTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#F6F5F1',
  },
  gameDate: {
    fontSize: 14,
    color: '#F6F5F1',
    marginTop: 5,
  },
});
