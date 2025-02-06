import React from 'react';
import { View, Text, Modal, StyleSheet, TouchableOpacity, Image, ScrollView } from 'react-native';

const GameInfoModal = ({ visible, onClose, game }) => {
  if (!game) return null;

  return (
    <Modal visible={visible} transparent animationType="slide">
      <View style={styles.modalContainer}>
        <View style={styles.modalContent}>
          {game.rawgDetails.background_image && (
            <Image source={{ uri: game.rawgDetails.background_image }} style={styles.modalImage} />
          )}
          <ScrollView>
            <Text style={styles.modalTitle}>{game.rawgDetails.name}</Text>
            <Text style={styles.modalText}>Release Date: {new Date(game.rawgDetails.released).toDateString()}</Text>
            <Text style={styles.modalText}>Status: {game.status}</Text>
            <Text style={styles.modalText}>Rating: {game.rawgDetails.rating}</Text>
            <Text style={styles.modalDescription}>{game.rawgDetails.description_raw}</Text>
          </ScrollView>
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <Text style={styles.closeButtonText}>Close</Text>
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  modalContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
  },
  modalContent: {
    width: '90%',
    height: '80%',
    backgroundColor: '#0F3460',
    borderRadius: 10,
    padding: 20,
    borderWidth: 2,
    borderColor: '#FFD700',
  },
  modalImage: {
    width: '100%',
    height: 200,
    borderRadius: 10,
    marginBottom: 10,
  },
  modalTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#FFD700',
    marginBottom: 10,
    textAlign: 'center',
  },
  modalText: {
    fontSize: 16,
    color: '#F6F5F1',
    marginBottom: 5,
  },
  modalDescription: {
    fontSize: 14,
    color: '#F6F5F1',
    marginTop: 10,
    textAlign: 'justify',
  },
  closeButton: {
    backgroundColor: '#13100F',
    padding: 10,
    borderRadius: 10,
    borderColor: '#FFD700',
    borderWidth: 2,
    alignItems: 'center',
    marginTop: 20,
  },
  closeButtonText: {
    color: '#FFD700',
    fontSize: 16,
  },
});

export default GameInfoModal;
