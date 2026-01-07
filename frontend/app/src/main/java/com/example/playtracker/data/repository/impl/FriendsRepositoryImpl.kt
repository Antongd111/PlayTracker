package com.example.playtracker.data.repository.impl

import com.example.playtracker.data.remote.mapper.*
import com.example.playtracker.data.remote.service.FriendsApi
import com.example.playtracker.data.repository.FriendsRepository
import com.example.playtracker.domain.model.FriendRequest
import com.example.playtracker.domain.model.User

class FriendsRepositoryImpl(
    private val api: FriendsApi
) : FriendsRepository {

    override suspend fun listFriends(bearer: String, userId: Int?): Result<List<User>> = runCatching {
        api.listFriends(userId = userId, bearer = bearer).body().orEmpty().map { it.toUser() }
    }

    override suspend fun listOutgoing(bearer: String, userId: Int): Result<List<FriendRequest>> = runCatching {
        val pending = api.listPending(userId = userId, bearer = bearer).body()
        pending?.outgoing.orEmpty().map { it.toDomain() }
    }

    override suspend fun listIncoming(bearer: String, userId: Int): Result<List<FriendRequest>> = runCatching {
        val pending = api.listPending(userId = userId, bearer = bearer).body()
        pending?.incoming.orEmpty().map { it.toDomain() }
    }

    override suspend fun sendRequest(toUserId: Int, bearer: String): Result<Unit> = runCatching {
        val res = api.sendFriendRequest(toUserId, bearer)
        if (!res.isSuccessful) error("HTTP ${res.code()}")
    }

    override suspend fun accept(friendshipId: Int, bearer: String): Result<Unit> = runCatching {
        val res = api.updateFriendshipStatus(friendshipId, "accept", bearer)
        if (!res.isSuccessful) error("HTTP ${res.code()}")
    }

    override suspend fun decline(friendshipId: Int, bearer: String): Result<Unit> = runCatching {
        val res = api.updateFriendshipStatus(friendshipId, "decline", bearer)
        if (!res.isSuccessful) error("HTTP ${res.code()}")
    }

    override suspend fun block(friendshipId: Int, bearer: String): Result<Unit> = runCatching {
        val res = api.updateFriendshipStatus(friendshipId, "block", bearer)
        if (!res.isSuccessful) error("HTTP ${res.code()}")
    }

    override suspend fun deleteFriendship(friendshipId: Int, bearer: String): Result<Unit> = runCatching {
        val res = api.deleteFriendship(friendshipId, bearer)
        if (!res.isSuccessful) error("HTTP ${res.code()}")
    }
}