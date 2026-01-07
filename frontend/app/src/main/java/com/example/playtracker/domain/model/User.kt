package com.example.playtracker.domain.model

data class User(
    val id: Int,
    val name: String,
    val avatarUrl: String?,
    val status: String? = null,
    val favoriteRawgId: Long? = null,
    val friendshipId: Int? = null
)

