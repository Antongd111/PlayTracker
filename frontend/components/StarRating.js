import React from 'react';
import { View, StyleSheet } from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';

const StarRating = ({ rating, maxStars = 5 }) => {
  const fullStars = Math.floor(rating);
  const halfStar = rating % 1 >= 0.5 ? 1 : 0;
  const emptyStars = maxStars - fullStars - halfStar;

  return (
    <View style={styles.starContainer}>
      {Array(fullStars)
        .fill()
        .map((_, index) => (
          <Icon key={`full-${index}`} name="star" size={15} color="#FFD700" />
        ))}
      {halfStar === 1 && <Icon name="star-half" size={15} color="#FFD700" />}
      {Array(emptyStars)
        .fill()
        .map((_, index) => (
          <Icon key={`empty-${index}`} name="star-outline" size={15} color="#FFD700" />
        ))}
    </View>
  );
};

const styles = StyleSheet.create({
  starContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
});

export default StarRating;
