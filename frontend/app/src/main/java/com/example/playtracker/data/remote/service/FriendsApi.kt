package com.example.playtracker.data.remote.service

import com.example.playtracker.data.remote.dto.friends.FriendDto
import com.example.playtracker.data.remote.dto.friends.PendingResponseDto
import com.example.playtracker.data.remote.dto.friends.SimpleOkDto
import retrofit2.Response
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.PATCH
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query

interface FriendsApi {

    @POST("friendships")
    suspend fun sendFriendRequest(
        @Query("to_user_id") toUserId: Int,
        @Header("Authorization") bearer: String
    ): Response<SimpleOkDto>

    @GET("friendships")
    suspend fun listFriends(
        @Query("status_filter") status: String = "accepted",
        @Query("user_id") userId: Int? = null,
        @Header("Authorization") bearer: String
    ): Response<List<FriendDto>>

    @GET("friendships")
    suspend fun listPending(
        @Query("status_filter") status: String = "pending",
        @Query("user_id") userId: Int,
        @Header("Authorization") bearer: String
    ): Response<PendingResponseDto>

    @PATCH("friendships/{friendshipId}")
    suspend fun updateFriendshipStatus(
        @Path("friendshipId") friendshipId: Int,
        @Query("action") action: String,
        @Header("Authorization") bearer: String
    ): Response<SimpleOkDto>

    @DELETE("friendships/{friendshipId}")
    suspend fun deleteFriendship(
        @Path("friendshipId") friendshipId: Int,
        @Header("Authorization") bearer: String
    ): Response<Unit>
}