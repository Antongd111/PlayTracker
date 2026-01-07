package com.example.playtracker.data.remote.mapper

import com.example.playtracker.data.remote.dto.friends.FriendDto
import com.example.playtracker.data.remote.dto.friends.IncomingReqDto
import com.example.playtracker.data.remote.dto.friends.OutgoingReqDto
import com.example.playtracker.data.remote.dto.user.UserLiteDto
import com.example.playtracker.domain.model.Friend
import com.example.playtracker.domain.model.FriendRequest
import com.example.playtracker.domain.model.User

fun UserLiteDto.toDomain() = User(
    id = id,
    name = username ?: "",
    avatarUrl = avatar_url
)

fun FriendDto.toUser() = User(
    id = id,
    name = username ?: "",
    avatarUrl = avatar_url,
    friendshipId = friendship_id
)

fun FriendDto.toDomain() = Friend(
    id = id,
    name = username ?: "",
    avatarUrl = avatar_url
)

fun IncomingReqDto.toDomain() = FriendRequest(
    friendshipId = friendship_id,
    requesterId = requester_id,
    otherUser = other_user.toDomain(),
    requestedAt = requested_at,
    status = status
)

fun OutgoingReqDto.toDomain() = FriendRequest(
    friendshipId = friendship_id,
    requesterId = requester_id,
    otherUser = other_user.toDomain(),
    requestedAt = requested_at,
    status = status
)
