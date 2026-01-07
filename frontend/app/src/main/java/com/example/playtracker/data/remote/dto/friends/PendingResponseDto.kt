package com.example.playtracker.data.remote.dto.friends

data class PendingResponseDto(
    val incoming: List<IncomingReqDto> = emptyList(),
    val outgoing: List<OutgoingReqDto> = emptyList()
)
