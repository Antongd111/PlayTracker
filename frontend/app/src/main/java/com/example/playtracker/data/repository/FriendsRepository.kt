package com.example.playtracker.data.repository

import com.example.playtracker.domain.model.FriendRequest
import com.example.playtracker.domain.model.User

interface FriendsRepository {
    suspend fun listFriends(bearer: String, userId: Int? = null): Result<List<User>>
    suspend fun listOutgoing(bearer: String, userId: Int): Result<List<FriendRequest>>
    suspend fun listIncoming(bearer: String, userId: Int): Result<List<FriendRequest>>
    suspend fun sendRequest(toUserId: Int, bearer: String): Result<Unit>
    suspend fun accept(friendshipId: Int, bearer: String): Result<Unit>
    suspend fun decline(friendshipId: Int, bearer: String): Result<Unit>
    suspend fun block(friendshipId: Int, bearer: String): Result<Unit>
    suspend fun deleteFriendship(friendshipId: Int, bearer: String): Result<Unit>
}