package com.example.playtracker.ui.viewmodel

import android.util.Log
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.playtracker.data.remote.dto.game.GameDetailDto
import com.example.playtracker.data.remote.service.RetrofitInstance
import com.example.playtracker.data.repository.ReviewsRepository
import com.example.playtracker.data.repository.UserGameRepository
import com.example.playtracker.data.repository.UserRepository
import com.example.playtracker.data.repository.impl.ReviewsRepositoryImpl
import com.example.playtracker.data.repository.impl.UserGameRepositoryImpl
import com.example.playtracker.data.repository.impl.UserRepositoryImpl
import com.example.playtracker.domain.model.GameReviews
import com.example.playtracker.domain.model.Review
import com.example.playtracker.domain.model.UserGame
import kotlinx.coroutines.launch

class GameDetailViewModel : ViewModel() {

    // --- Dependencias (sin DI) ---
    private val gameApi = RetrofitInstance.gameApi
    private val userApi = RetrofitInstance.userApi
    private val userGameRepo: UserGameRepository =
        UserGameRepositoryImpl(
            userGameApi = RetrofitInstance.userGameApi,
            gameApi = gameApi
        )
    private val reviewsRepo: ReviewsRepository =
        ReviewsRepositoryImpl(RetrofitInstance.reviewsApi)

    private val userRepo: UserRepository =
        UserRepositoryImpl(RetrofitInstance.userApi, RetrofitInstance.friendsApi)

    // --- Estado ---
    var gameDetail by mutableStateOf<GameDetailDto?>(null)
        private set

    var userGame by mutableStateOf<UserGame?>(null)
        private set

    var isLoading by mutableStateOf(false)
        private set

    var error by mutableStateOf<String?>(null)
        private set

    // --- Reseñas ---
    var gameReviews by mutableStateOf<GameReviews?>(null)
        private set
    var reviews by mutableStateOf<List<Review>>(emptyList())
        private set
    var isLoadingReviews by mutableStateOf(false)
        private set
    var reviewsError by mutableStateOf<String?>(null)
        private set

    // --- Favorito (estado local; no usamos el User devuelto por setFavorite) ---
    var favoriteGameId by mutableStateOf<Long?>(null)
        private set
    var isTogglingFavorite by mutableStateOf(false)
        private set
    var favoriteError by mutableStateOf<String?>(null)
        private set

    // --- Lógica ---
    fun loadReviews(gameId: Long, bearer: String) {
        viewModelScope.launch {
            isLoadingReviews = true
            reviewsError = null
            reviewsRepo.getReviews(gameId = gameId, limit = 20, bearer = bearer)
                .onSuccess { gr ->
                    gameReviews = gr
                    reviews = gr.reviews
                }
                .onFailure { e ->
                    reviewsError = e.message ?: "No se pudieron cargar las reseñas"
                }
            isLoadingReviews = false
        }
    }

    fun loadGameDetail(gameId: Long) {
        viewModelScope.launch {
            isLoading = true
            error = null
            runCatching { gameApi.getGameDetails(gameId) }
                .onSuccess { dto ->
                    gameDetail = dto
                    Log.d("GameDetail", dto.toString())
                }
                .onFailure { e ->
                    error = e.message ?: "Error al cargar detalles"
                    Log.e("GameDetail", "Error cargando detalles", e)
                }
            isLoading = false
        }
    }

    fun getUserGame(userId: Int, gameId: Long) {
        viewModelScope.launch {
            runCatching { userGameRepo.getUserGame(userId, gameId) }
                .onSuccess { ug -> userGame = ug }
        }
    }

    fun updateGameStatus(userId: Int, gameRawgId: Long, newStatus: String) {
        viewModelScope.launch {
            if (newStatus.equals("No seguido", ignoreCase = true)) {
                runCatching { userGameRepo.deleteUserGame(userId, gameRawgId) }
                    .onSuccess {
                        userGame = null
                        error = null
                    }
                    .onFailure { error = "Error al eliminar el juego de tu biblioteca" }
            } else {
                runCatching { userGameRepo.upsertUserGame(userId, gameRawgId, newStatus) }
                    .onSuccess { ug -> userGame = ug }
                    .onFailure { error = "Error al actualizar estado del juego" }
            }
        }
    }

    // --- Favorito ---

    /** Carga el favorito actual del usuario para mostrar la estrella resaltada al entrar. */
    fun loadMyFavorite(bearer: String) {
        viewModelScope.launch {
            runCatching { userRepo.me(bearer) }
                .onSuccess { me -> favoriteGameId = me.favoriteRawgId }
                .onFailure { /* silencioso */ }
        }
    }

    /** Marca este juego como favorito. No usamos el User que devuelve; solo actualizamos estado local. */
    fun setFavorite(userId: Int, bearer: String, gameRawgId: Long) {
        if (isTogglingFavorite) return
        viewModelScope.launch {
            isTogglingFavorite = true
            favoriteError = null
            runCatching {
                userRepo.setFavorite(
                    userId = userId,
                    gameRawgId,
                    bearer = bearer
                )
            }.onSuccess {
                favoriteGameId = gameRawgId
            }.onFailure { e ->
                favoriteError = e.message ?: "No se pudo actualizar el favorito"
            }
            isTogglingFavorite = false
        }
    }

    /** Quita el favorito (por si lo quieres usar como toggle en otro momento). */
    fun clearFavorite(userId: Int, bearer: String) {
        if (isTogglingFavorite) return
        viewModelScope.launch {
            isTogglingFavorite = true
            favoriteError = null
            runCatching {
                userRepo.setFavorite(
                    userId = userId,
                    null,
                    bearer = bearer
                )
            }.onSuccess {
                favoriteGameId = null
            }.onFailure { e ->
                favoriteError = e.message ?: "No se pudo limpiar el favorito"
            }
            isTogglingFavorite = false
        }
    }
}