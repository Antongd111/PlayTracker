import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import Icon from 'react-native-vector-icons/Ionicons';
import { View, Text } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';

import HomeScreen from '../screens/HomeScreen';
import ExploreScreen from '../screens/ExploreScreen';
import ProfileScreen from '../screens/ProfileScreen';

const Tab = createBottomTabNavigator();

function AppNavigator() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName;

          if (route.name === 'Home') {
            iconName = focused ? 'home' : 'home-outline';
          } else if (route.name === 'Explore') {
            iconName = focused ? 'search' : 'search-outline';
          } else if (route.name === 'Profile') {
            iconName = focused ? 'person' : 'person-outline';
          }

          return (
            <View style={{ alignItems: 'center' }}>
              <Icon name={iconName} size={size} color={color} />
            </View>
          );
        },
        tabBarActiveTintColor: '#FFD700', // Amarillo neón
        tabBarInactiveTintColor: '#00D9FF', // Azul neón
        tabBarStyle: {
          backgroundColor: '#1A1A2E',
          borderTopWidth: 0,
          elevation: 10,
          shadowColor: '#FFD700',
          shadowOpacity: 0.6,
          shadowRadius: 15,
        },
        tabBarLabelStyle: {
          fontSize: 12,
          fontWeight: 'bold',
          color: '#00D9FF',
        },
        tabBarBackground: () => (
          <LinearGradient
            colors={['#16213E', '#0F3460']}
            style={{ flex: 1 }}
          />
        ),
        headerShown: false,
      })}
    >
      <Tab.Screen
        name="Home"
        component={HomeScreen}
        options={{
          tabBarLabel: ({ focused }) => (
            <Text style={{ color: focused ? '#FFD700' : '#00D9FF' }}>Home</Text>
          ),
        }}
      />
      <Tab.Screen
        name="Explore"
        component={ExploreScreen}
        options={{
          tabBarLabel: ({ focused }) => (
            <Text style={{ color: focused ? '#FFD700' : '#00D9FF' }}>Explore</Text>
          ),
        }}
      />
      <Tab.Screen
        name="Profile"
        component={ProfileScreen}
        options={{
          tabBarLabel: ({ focused }) => (
            <Text style={{ color: focused ? '#FFD700' : '#00D9FF' }}>Profile</Text>
          ),
        }}
      />
    </Tab.Navigator>
  );
}

export default AppNavigator;
