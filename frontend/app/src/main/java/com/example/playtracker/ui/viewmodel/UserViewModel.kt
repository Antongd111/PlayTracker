package com.example.playtracker.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.playtracker.data.remote.service.RetrofitInstance
import com.example.playtracker.data.repository.FriendsRepository
import com.example.playtracker.data.repository.UserGameRepository
import com.example.playtracker.data.repository.UserRepository
import com.example.playtracker.data.repository.impl.FriendsRepositoryImpl
import com.example.playtracker.data.repository.impl.UserGameRepositoryImpl
import com.example.playtracker.data.repository.impl.UserRepositoryImpl
import com.example.playtracker.domain.model.Friend
import com.example.playtracker.domain.model.User
import com.example.playtracker.domain.model.UserGame
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class UserUiState(
    val loading: Boolean = true,
    val user: User? = null,
    val favorite: UserGame? = null,
    val completed: List<UserGame> = emptyList(),
    val friends: List<Friend> = emptyList(),
    val isOwn: Boolean = false,
    val friendState: FriendState = FriendState.NONE,
    val userGames: List<UserGame> = emptyList(),
    val reviews: List<UserGame> = emptyList(),
    val workingFriend: Boolean = false,
    val error: String? = null,

    // ✅ IDs necesarios para borrar/cancelar con el nuevo backend
    val outgoingFriendshipId: Int? = null,
    val friendsFriendshipId: Int? = null
)

class UserViewModel : ViewModel() {

    private val users: UserRepository =
        UserRepositoryImpl(RetrofitInstance.userApi, RetrofitInstance.friendsApi)

    private val userGamesRepo: UserGameRepository =
        UserGameRepositoryImpl(RetrofitInstance.userGameApi, RetrofitInstance.gameApi)

    private val friendsRepo: FriendsRepository =
        FriendsRepositoryImpl(RetrofitInstance.friendsApi)

    private val _ui = MutableStateFlow(UserUiState())
    val ui: StateFlow<UserUiState> = _ui

    fun load(userId: Int, token: String?) {
        viewModelScope.launch {
            _ui.value = UserUiState(loading = true)
            val bearer = token?.let { "Bearer $it" }

            runCatching {
                val meId = if (bearer != null) users.me(bearer).id else null
                val user = users.getUser(userId)

                val allUG: List<UserGame> = userGamesRepo.listByUser(userId)
                val completedUG = allUG.filter { it.status?.equals("Completado", ignoreCase = true) == true }

                val favoriteUG: UserGame? = user.favoriteRawgId?.let { favId ->
                    allUG.firstOrNull { it.gameRawgId == favId }
                }

                val reviewsUG = allUG.filter { !it.notes.isNullOrBlank() }

                val friends = if (bearer != null) users.getFriendsOf(userId, bearer) else emptyList()
                val isOwn = meId != null && meId == user.id

                // --- Estado amistad (nuevo repo: listFriends/listOutgoing requieren userId) ---
                var friendState = FriendState.NONE
                var outgoingFriendshipId: Int? = null
                var friendsFriendshipId: Int? = null

                if (!isOwn && bearer != null && meId != null) {
                    val currentFriends = friendsRepo.listFriends(bearer = bearer, userId = meId).getOrElse { emptyList() }
                    val outgoing = friendsRepo.listOutgoing(bearer = bearer, userId = meId).getOrElse { emptyList() }

                    val friendHit = currentFriends.firstOrNull { it.id == user.id }
                    val outgoingHit = outgoing.firstOrNull { it.otherUser.id == user.id }

                    when {
                        friendHit != null -> {
                            friendState = FriendState.FRIENDS
                            friendsFriendshipId = friendHit.friendshipId
                        }
                        outgoingHit != null -> {
                            friendState = FriendState.PENDING_SENT
                            outgoingFriendshipId = outgoingHit.friendshipId
                        }
                        else -> {
                            friendState = FriendState.NONE
                        }
                    }
                }

                LoadedBundle(
                    user = user,
                    completed = completedUG,
                    favorite = favoriteUG,
                    friends = friends,
                    isOwn = isOwn,
                    friendState = friendState,
                    allUG = allUG,
                    reviews = reviewsUG,
                    outgoingFriendshipId = outgoingFriendshipId,
                    friendsFriendshipId = friendsFriendshipId,
                    token = token
                )
            }.onSuccess { b ->
                _ui.value = UserUiState(
                    loading = false,
                    user = b.user,
                    completed = b.completed,
                    favorite = b.favorite,
                    friends = b.friends,
                    isOwn = b.isOwn,
                    friendState = b.friendState,
                    userGames = b.allUG,
                    reviews = b.reviews,
                    outgoingFriendshipId = b.outgoingFriendshipId,
                    friendsFriendshipId = b.friendsFriendshipId
                )
            }.onFailure { e ->
                _ui.value = UserUiState(loading = false, error = e.message)
            }
        }
    }

    fun toggleFriendAction(bearer: String, myUserId: Int, onSnack: (String) -> Unit = {}) {
        val u = _ui.value.user ?: return
        if (_ui.value.isOwn) return
        if (_ui.value.workingFriend) return

        viewModelScope.launch {
            _ui.update { it.copy(workingFriend = true, error = null) }

            when (_ui.value.friendState) {

                FriendState.NONE -> {
                    friendsRepo.sendRequest(toUserId = u.id, bearer = bearer)
                        .onSuccess {
                            onSnack("Solicitud enviada")
                            refreshFriendState(bearer = bearer, myUserId = myUserId, otherUserId = u.id)
                        }
                        .onFailure { e ->
                            _ui.update { it.copy(workingFriend = false, error = e.message) }
                            onSnack("No se pudo enviar: ${e.message ?: ""}")
                        }
                }

                FriendState.PENDING_SENT -> {
                    val fid = _ui.value.outgoingFriendshipId
                    if (fid == null) {
                        _ui.update { it.copy(workingFriend = false) }
                        onSnack("No tengo el id de la solicitud (refresca)")
                        refreshFriendState(bearer = bearer, myUserId = myUserId, otherUserId = u.id)
                        return@launch
                    }

                    friendsRepo.deleteFriendship(friendshipId = fid, bearer = bearer)
                        .onSuccess {
                            onSnack("Solicitud cancelada")
                            refreshFriendState(bearer = bearer, myUserId = myUserId, otherUserId = u.id)
                        }
                        .onFailure { e ->
                            _ui.update { it.copy(workingFriend = false, error = e.message) }
                            onSnack("No se pudo cancelar: ${e.message ?: ""}")
                        }
                }

                FriendState.FRIENDS -> {
                    val fid = _ui.value.friendsFriendshipId
                    if (fid == null) {
                        _ui.update { it.copy(workingFriend = false) }
                        onSnack("No puedo borrar amistad: falta friendshipId (backend debe devolverlo)")
                        refreshFriendState(bearer = bearer, myUserId = myUserId, otherUserId = u.id)
                        return@launch
                    }

                    friendsRepo.deleteFriendship(friendshipId = fid, bearer = bearer)
                        .onSuccess {
                            onSnack("Amistad eliminada")
                            refreshFriendState(bearer = bearer, myUserId = myUserId, otherUserId = u.id)
                        }
                        .onFailure { e ->
                            _ui.update { it.copy(workingFriend = false, error = e.message) }
                            onSnack("No se pudo eliminar: ${e.message ?: ""}")
                        }
                }
            }
        }
    }

    fun updateProfile(newName: String, newStatus: String?, bearer: String) {
        val u = _ui.value.user ?: return
        if (!_ui.value.isOwn) return

        viewModelScope.launch {
            _ui.update { it.copy(loading = true, error = null) }

            runCatching {
                users.updateUserProfile(
                    name = newName,
                    status = newStatus,
                    bearer = bearer
                )
            }.onSuccess { updated ->
                _ui.update { it.copy(loading = false, user = updated) }
            }.onFailure { e ->
                _ui.update { it.copy(loading = false, error = e.message) }
            }
        }
    }

    private fun refreshFriendState(bearer: String, myUserId: Int, otherUserId: Int) {
        viewModelScope.launch {
            val currentFriends = friendsRepo.listFriends(bearer = bearer, userId = myUserId).getOrElse { emptyList() }
            val outgoing = friendsRepo.listOutgoing(bearer = bearer, userId = myUserId).getOrElse { emptyList() }

            val friendHit = currentFriends.firstOrNull { it.id == otherUserId }
            val outgoingHit = outgoing.firstOrNull { it.otherUser.id == otherUserId }

            _ui.update { curr ->
                when {
                    friendHit != null -> curr.copy(
                        workingFriend = false,
                        friendState = FriendState.FRIENDS,
                        friendsFriendshipId = friendHit.friendshipId,
                        outgoingFriendshipId = null
                    )
                    outgoingHit != null -> curr.copy(
                        workingFriend = false,
                        friendState = FriendState.PENDING_SENT,
                        outgoingFriendshipId = outgoingHit.friendshipId,
                        friendsFriendshipId = null
                    )
                    else -> curr.copy(
                        workingFriend = false,
                        friendState = FriendState.NONE,
                        outgoingFriendshipId = null,
                        friendsFriendshipId = null
                    )
                }
            }
        }
    }

    private data class LoadedBundle(
        val user: User,
        val completed: List<UserGame>,
        val favorite: UserGame?,
        val friends: List<Friend>,
        val isOwn: Boolean,
        val friendState: FriendState,
        val allUG: List<UserGame>,
        val reviews: List<UserGame>,
        val outgoingFriendshipId: Int?,
        val friendsFriendshipId: Int?,
        val token: String?
    )
}
