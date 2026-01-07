package com.example.playtracker.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.playtracker.domain.model.FriendRequest
import com.example.playtracker.domain.model.User
import com.example.playtracker.data.repository.FriendsRepository
import com.example.playtracker.data.repository.UserRepository
import com.example.playtracker.data.repository.impl.FriendsRepositoryImpl
import com.example.playtracker.data.repository.impl.UserRepositoryImpl
import com.example.playtracker.data.remote.service.RetrofitInstance
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

enum class FriendState { NONE, PENDING_SENT, FRIENDS }

data class SocialUiState(
    val workingFor: Set<Int> = emptySet(),
    val states: Map<Int, FriendState> = emptyMap(),
    val error: String? = null,

    val incoming: List<FriendRequest> = emptyList(),
    val workingIncoming: Set<Int> = emptySet(),

    val results: List<User> = emptyList(),
    val isSearching: Boolean = false,

    val outgoingFriendshipByUserId: Map<Int, Int> = emptyMap(),
    val incomingFriendshipByUserId: Map<Int, Int> = emptyMap(),
    val friendsFriendshipByUserId: Map<Int, Int> = emptyMap()
)

class SocialViewModel : ViewModel() {

    private val users: UserRepository =
        UserRepositoryImpl(
            users = RetrofitInstance.userApi,
            friends = RetrofitInstance.friendsApi
        )

    private val friends: FriendsRepository =
        FriendsRepositoryImpl(RetrofitInstance.friendsApi)

    private val _ui = MutableStateFlow(SocialUiState())
    val ui: StateFlow<SocialUiState> = _ui

    fun search(query: String) = viewModelScope.launch {
        if (query.isBlank()) {
            _ui.update { it.copy(results = emptyList(), isSearching = false, error = null) }
            return@launch
        }

        _ui.update { it.copy(isSearching = true, error = null) }

        runCatching { users.searchUsers(query) }
            .onSuccess { list ->
                _ui.update { curr ->
                    val next = curr.states.toMutableMap()
                    list.forEach { if (it.id !in next) next[it.id] = FriendState.NONE }
                    curr.copy(results = list, states = next, isSearching = true)
                }
            }
            .onFailure { e ->
                _ui.update { it.copy(error = e.message, results = emptyList(), isSearching = true) }
            }
    }

    fun hydrateStatesForResults(bearer: String, myUserId: Int) = viewModelScope.launch {
        val resultIds = _ui.value.results.map { it.id }
        if (resultIds.isEmpty()) return@launch

        val friendsList = friends.listFriends(bearer = bearer, userId = myUserId).getOrElse { emptyList() }
        val outgoing = friends.listOutgoing(bearer = bearer, userId = myUserId).getOrElse { emptyList() }

        _ui.update { curr ->
            val nextStates = curr.states.toMutableMap()

            val friendsMap = friendsList
                .filter { it.friendshipId != null }
                .associate { it.id to it.friendshipId!! }

            friendsMap.keys.forEach { otherId ->
                if (otherId in resultIds) nextStates[otherId] = FriendState.FRIENDS
            }

            val outMap = outgoing.associate { req ->
                req.otherUser.id to req.friendshipId
            }

            outMap.keys.forEach { otherId ->
                if (otherId in resultIds) nextStates[otherId] = FriendState.PENDING_SENT
            }

            curr.copy(
                states = nextStates,
                outgoingFriendshipByUserId = outMap,
                friendsFriendshipByUserId = friendsMap
            )
        }
    }

    fun loadIncoming(bearer: String, myUserId: Int) = viewModelScope.launch {
        val inc = friends.listIncoming(bearer = bearer, userId = myUserId).getOrElse { emptyList() }

        val inMap = inc.associate { req ->
            req.otherUser.id to req.friendshipId
        }

        _ui.update { it.copy(incoming = inc, incomingFriendshipByUserId = inMap) }
    }

    fun toggleFriendAction(userId: Int, bearer: String, myUserId: Int, onSnack: (String) -> Unit) {
        val current = _ui.value.states[userId] ?: FriendState.NONE
        if (_ui.value.workingFor.contains(userId)) return

        viewModelScope.launch {
            _ui.update { it.copy(workingFor = it.workingFor + userId, error = null) }

            when (current) {

                FriendState.NONE -> {
                    friends.sendRequest(toUserId = userId, bearer = bearer)
                        .onSuccess {
                            _ui.update {
                                it.copy(
                                    workingFor = it.workingFor - userId,
                                    states = it.states + (userId to FriendState.PENDING_SENT)
                                )
                            }
                            hydrateStatesForResults(bearer, myUserId)
                            onSnack("Solicitud enviada")
                        }
                        .onFailure { e ->
                            _ui.update { it.copy(workingFor = it.workingFor - userId, error = e.message) }
                            onSnack("No se pudo enviar: ${e.message ?: ""}")
                        }
                }

                FriendState.PENDING_SENT -> {
                    val friendshipId = _ui.value.outgoingFriendshipByUserId[userId]
                    if (friendshipId == null) {
                        _ui.update { it.copy(workingFor = it.workingFor - userId) }
                        onSnack("No tengo el id de la solicitud (refresca la lista)")
                        hydrateStatesForResults(bearer, myUserId)
                        return@launch
                    }

                    friends.deleteFriendship(friendshipId = friendshipId, bearer = bearer)
                        .onSuccess {
                            _ui.update {
                                it.copy(
                                    workingFor = it.workingFor - userId,
                                    states = it.states + (userId to FriendState.NONE),
                                    outgoingFriendshipByUserId = it.outgoingFriendshipByUserId - userId
                                )
                            }
                            onSnack("Solicitud cancelada")
                        }
                        .onFailure { e ->
                            hydrateStatesForResults(bearer, myUserId)
                            _ui.update { it.copy(workingFor = it.workingFor - userId, error = e.message) }
                            onSnack("No se pudo cancelar: ${e.message ?: ""}")
                        }
                }

                FriendState.FRIENDS -> {
                    val friendshipId = _ui.value.friendsFriendshipByUserId[userId]
                    if (friendshipId == null) {
                        _ui.update { it.copy(workingFor = it.workingFor - userId) }
                        onSnack("No puedo borrar amistad: falta friendshipId (backend debe devolverlo)")
                        hydrateStatesForResults(bearer, myUserId)
                        return@launch
                    }

                    friends.deleteFriendship(friendshipId = friendshipId, bearer = bearer)
                        .onSuccess {
                            _ui.update {
                                it.copy(
                                    workingFor = it.workingFor - userId,
                                    states = it.states + (userId to FriendState.NONE),
                                    friendsFriendshipByUserId = it.friendsFriendshipByUserId - userId
                                )
                            }
                            onSnack("Amistad eliminada")
                        }
                        .onFailure { e ->
                            hydrateStatesForResults(bearer, myUserId)
                            _ui.update { it.copy(workingFor = it.workingFor - userId, error = e.message) }
                            onSnack("No se pudo eliminar: ${e.message ?: ""}")
                        }
                }
            }
        }
    }

    fun acceptIncoming(fromUserId: Int, bearer: String, myUserId: Int, onSnack: (String) -> Unit) {
        viewModelScope.launch {
            _ui.update { it.copy(workingIncoming = it.workingIncoming + fromUserId) }

            val friendshipId = _ui.value.incomingFriendshipByUserId[fromUserId]
            if (friendshipId == null) {
                _ui.update { it.copy(workingIncoming = it.workingIncoming - fromUserId) }
                onSnack("No tengo el id de la solicitud entrante (refresca)")
                loadIncoming(bearer, myUserId)
                return@launch
            }

            friends.accept(friendshipId = friendshipId, bearer = bearer)
                .onSuccess {
                    _ui.update { curr ->
                        val newList = curr.incoming.filter { it.otherUser.id != fromUserId }
                        curr.copy(
                            workingIncoming = curr.workingIncoming - fromUserId,
                            incoming = newList,
                            states = curr.states + (fromUserId to FriendState.FRIENDS),
                            incomingFriendshipByUserId = curr.incomingFriendshipByUserId - fromUserId
                        )
                    }
                    onSnack("Solicitud aceptada")
                    hydrateStatesForResults(bearer, myUserId)
                }
                .onFailure { e ->
                    _ui.update { it.copy(workingIncoming = it.workingIncoming - fromUserId, error = e.message) }
                    onSnack("No se pudo aceptar: ${e.message ?: ""}")
                }
        }
    }

    fun declineIncoming(fromUserId: Int, bearer: String, myUserId: Int, onSnack: (String) -> Unit) {
        viewModelScope.launch {
            _ui.update { it.copy(workingIncoming = it.workingIncoming + fromUserId) }

            val friendshipId = _ui.value.incomingFriendshipByUserId[fromUserId]
            if (friendshipId == null) {
                _ui.update { it.copy(workingIncoming = it.workingIncoming - fromUserId) }
                onSnack("No tengo el id de la solicitud entrante (refresca)")
                loadIncoming(bearer, myUserId)
                return@launch
            }

            friends.decline(friendshipId = friendshipId, bearer = bearer)
                .onSuccess {
                    _ui.update { curr ->
                        val newList = curr.incoming.filter { it.otherUser.id != fromUserId }
                        curr.copy(
                            workingIncoming = curr.workingIncoming - fromUserId,
                            incoming = newList,
                            states = curr.states + (fromUserId to FriendState.NONE),
                            incomingFriendshipByUserId = curr.incomingFriendshipByUserId - fromUserId
                        )
                    }
                    onSnack("Solicitud rechazada")
                    hydrateStatesForResults(bearer, myUserId)
                }
                .onFailure { e ->
                    _ui.update { it.copy(workingIncoming = it.workingIncoming - fromUserId, error = e.message) }
                    onSnack("No se pudo rechazar: ${e.message ?: ""}")
                }
        }
    }
}
