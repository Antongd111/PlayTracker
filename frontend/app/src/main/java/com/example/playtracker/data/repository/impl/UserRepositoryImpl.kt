package com.example.playtracker.data.repository.impl

import com.example.playtracker.data.remote.dto.user.FavouriteRequestDto
import com.example.playtracker.data.remote.dto.user.UpdateUserDto
import com.example.playtracker.data.remote.mapper.*
import com.example.playtracker.data.remote.service.UserApi
import com.example.playtracker.data.remote.service.FriendsApi
import com.example.playtracker.domain.model.User
import com.example.playtracker.domain.model.Friend
import com.example.playtracker.data.repository.UserRepository
import com.example.playtracker.domain.model.GamePreview

class UserRepositoryImpl(
    private val users: UserApi,
    private val friends: FriendsApi
) : UserRepository {
    override suspend fun me(bearer: String): User =
        users.getCurrentUser(bearer).toDomain()

    override suspend fun getUser(id: Int): User =
        users.getUserById(id).toDomain()

    override suspend fun searchUsers(query: String): List<User> =
        users.searchUsers(query).map { it.toDomain() }

    override suspend fun getFriendsOf(userId: Int, bearer: String): List<Friend> =
        users.listFriendsOf(userId, bearer)
            .map { it.toDomain() }

    override suspend fun updateUserProfile(name: String, status: String?, bearer: String): User {
        val me = users.getCurrentUser(bearer)
        val updated = users.updateUserById(
            id = me.id,
            body = UpdateUserDto(name = name, status = status),
            token = bearer
        )
        return updated.toDomain()
    }

    override suspend fun getFriendGames(id: Int): List<GamePreview> =
        users.getFriendsGames(id).map { dto ->
        GamePreview(
            id = dto.id,
            title = dto.title,
            imageUrl = dto.imageUrl,
            year = dto.year ?: 0,
        )
    }

    override suspend fun setFavorite(userId: Int, gameRawgId: Long?, bearer: String): User {
        return users.setFavoriteById(userId, FavouriteRequestDto(gameRawgId), bearer).toDomain()
    }
}