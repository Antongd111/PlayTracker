import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, Image, FlatList, ActivityIndicator } from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import AsyncStorage from '@react-native-async-storage/async-storage';
import api from '../services/api';

export default function ProfileScreen() {
  const insets = useSafeAreaInsets();
  
  // User data
  const [username, setUsername] = useState('');
  const [status, setStatus] = useState('');
  const [loading, setLoading] = useState(true);

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
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUserData();
  }, []);

  if (loading) {
    return <ActivityIndicator size="large" style={styles.loadingIndicator} />;
  }

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

      <View style={styles.optionsContainer}>
        <View style={styles.option}>
          <Icon name="checkmark-done-outline" size={25} color="#6A5ACD" />
          <Text style={styles.optionText}>Completed</Text>
        </View>
        <View style={styles.option}>
          <Icon name="pulse-outline" size={25} color="#6A5ACD" />
          <Text style={styles.optionText}>Playing</Text>
        </View>
        <View style={styles.option}>
          <Icon name="receipt-outline" size={25} color="#6A5ACD" />
          <Text style={styles.optionText}>To play list</Text>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {

  },
  profileHeader: {
    paddingBottom: '5%',
    paddingTop: '5%',
    display: 'flex',
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#cfcfcf',
  },
  profileIconContainer: {
    marginLeft: '5%',
    marginRight: '3%',
  },
  profileText: {
    display: 'flex',
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
  optionsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    width: '100%',
    alignSelf: 'center',
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
});