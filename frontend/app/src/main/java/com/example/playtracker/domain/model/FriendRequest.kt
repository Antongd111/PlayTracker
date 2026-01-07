package com.example.playtracker.domain.model

enum class FriendState { NONE, PENDING_SENT, FRIENDS }

data class FriendRequest(
    val friendshipId: Int,
    val requesterId: Int,
    val otherUser: User,
    val requestedAt: String,
    val status: String
)
