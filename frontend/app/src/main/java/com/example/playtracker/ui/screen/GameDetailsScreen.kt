package com.example.playtracker.ui.screen

import android.widget.Toast
import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Star
import androidx.compose.material.icons.filled.StarHalf
import androidx.compose.material.icons.outlined.Star
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextDecoration
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import coil.compose.rememberAsyncImagePainter
import com.example.playtracker.R
import com.example.playtracker.data.local.datastore.UserPreferences
import com.example.playtracker.data.remote.service.RetrofitInstance
import com.example.playtracker.data.repository.impl.ReviewsRepositoryImpl
import com.example.playtracker.domain.model.Review
import com.example.playtracker.ui.viewmodel.GameDetailViewModel
import kotlinx.coroutines.flow.firstOrNull
import kotlinx.coroutines.launch
import kotlin.math.roundToInt
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.rememberScrollState
import androidx.compose.material.icons.filled.SportsEsports
import androidx.compose.material.icons.filled.Computer
import androidx.compose.material.icons.filled.PhoneIphone
import androidx.compose.material.icons.filled.Tablet
import androidx.compose.material3.AssistChip
import androidx.compose.material3.AssistChipDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import java.time.LocalDate
import java.time.format.DateTimeFormatter

private fun formatDate(date: String?): String {
    if (date.isNullOrBlank()) return "Sin fecha"
    // Espera "YYYY-MM-DD"
    val parts = date.split("-")
    return if (parts.size == 3) "${parts[2]}-${parts[1]}-${parts[0]}" else date
}

private fun abbrevPlatform(name: String): String {
    val n = name.lowercase()
    return when {
        "playstation 5" in n || "ps5" in n -> "PS5"
        "playstation 4" in n || "ps4" in n -> "PS4"
        "playstation 3" in n || "ps3" in n -> "PS3"
        "xbox series" in n -> "XSX"
        "xbox one" in n -> "XONE"
        "xbox 360" in n -> "X360"
        "nintendo switch" in n || "switch" in n -> "SW"
        "wii u" in n -> "WiiU"
        "wii" in n -> "Wii"
        "pc" in n -> "PC"
        "ios" in n -> "iOS"
        "android" in n -> "Android"
        "mac" in n || "macos" in n -> "macOS"
        "linux" in n -> "Linux"
        else -> name.take(10)
    }
}

@Composable
private fun platformContainerColor(name: String) = when {
    name.contains("PlayStation", true) -> MaterialTheme.colorScheme.primary.copy(alpha = 0.12f)
    name.contains("Xbox", true)        -> MaterialTheme.colorScheme.tertiary.copy(alpha = 0.12f)
    name.contains("Switch", true) ||
            name.contains("Nintendo", true)    -> MaterialTheme.colorScheme.error.copy(alpha = 0.12f)
    name.contains("PC", true) ||
            name.contains("Linux", true) ||
            name.contains("mac", true)         -> MaterialTheme.colorScheme.secondary.copy(alpha = 0.12f)
    else                               -> MaterialTheme.colorScheme.surfaceVariant
}

@Composable
private fun platformLabelColor() = MaterialTheme.colorScheme.onSurface

@Composable
private fun platformIcon(name: String) = when {
    name.contains("PC", true) ||
            name.contains("Linux", true) ||
            name.contains("mac", true) -> Icons.Filled.Computer
    name.contains("iOS", true) ||
            name.contains("Android", true) -> Icons.Filled.PhoneIphone
    name.contains("Switch", true) ||
            name.contains("Nintendo", true) -> Icons.Filled.Tablet
    else -> Icons.Filled.SportsEsports
}

@Composable
private fun PlatformChip(name: String) {
    AssistChip(
        onClick = { /* no-op */ },
        label = { Text(abbrevPlatform(name)) },
        leadingIcon = {
            Icon(
                imageVector = platformIcon(name),
                contentDescription = null
            )
        },
        colors = AssistChipDefaults.assistChipColors(
            labelColor = platformLabelColor(),
            containerColor = platformContainerColor(name)
        )
    )
}

@Composable
private fun PlatformsSection(platforms: List<String>) {
    if (platforms.isEmpty()) return
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp)
    ) {
        Spacer(Modifier.height(8.dp))
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .horizontalScroll(rememberScrollState()),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            platforms.forEach { p -> PlatformChip(p) }
        }
    }
}

@Composable
private fun TextTagChip(text: String) {
    AssistChip(
        onClick = { /* no-op */ },
        label = { Text(text) },
        colors = AssistChipDefaults.assistChipColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant,
            labelColor = MaterialTheme.colorScheme.onSurfaceVariant
        )
    )
}

@Composable
private fun GenresSection(genres: List<String>) {
    if (genres.isEmpty()) return
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .horizontalScroll(rememberScrollState()),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            genres.forEach { g -> TextTagChip(g) }
        }
    }
}

@Composable
fun GameDetailScreen(
    gameId: Long
) {
    val viewModel: GameDetailViewModel = androidx.lifecycle.viewmodel.compose.viewModel(
        key = "GameDetailVM_$gameId"
    )

    var showConfirmRemove by remember { mutableStateOf(false) }
    var pendingStatus by remember { mutableStateOf<String?>(null) }

    val context = LocalContext.current
    val prefs = remember { UserPreferences(context) }
    var userId by remember { mutableStateOf<Int?>(null) }
    val token by prefs.tokenFlow.collectAsState(initial = null)
    val bearer: String? = token?.let { "Bearer $it" }

    val reviewsRepo = remember { ReviewsRepositoryImpl(RetrofitInstance.reviewsApi) }
    val scope = rememberCoroutineScope()

    // Cargas iniciales
    LaunchedEffect(gameId, bearer) {
        viewModel.loadGameDetail(gameId)
        if (bearer != null) {
            viewModel.loadReviews(gameId, bearer)
            viewModel.loadMyFavorite(bearer) // <-- para resaltar la estrella al entrar
        }
    }
    LaunchedEffect(Unit) {
        userId = prefs.userIdFlow.firstOrNull()
        userId?.let { uid -> viewModel.getUserGame(uid, gameId) }
    }
    LaunchedEffect(userId) {
        userId?.let { uid -> viewModel.getUserGame(uid, gameId) }
    }

    // Feedback al marcar favorito
    LaunchedEffect(viewModel.favoriteGameId) {
        if (bearer != null && viewModel.favoriteGameId == gameId) {
            Toast.makeText(context, "Marcado como favorito", Toast.LENGTH_SHORT).show()
        }
    }

    val gameDetail = viewModel.gameDetail
    val userGame = viewModel.userGame
    val isLoading = viewModel.isLoading
    val error = viewModel.error

    when {
        isLoading -> {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                CircularProgressIndicator()
            }
        }
        error != null -> {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                Text("Error: $error")
            }
        }
        gameDetail != null -> {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .background(MaterialTheme.colorScheme.background)
                    .verticalScroll(rememberScrollState())
                    .padding(WindowInsets.systemBars.asPaddingValues())
            ) {
                // -------- Cabecera con imagen + botón favorito --------
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(200.dp)
                ) {
                    Image(
                        painter = rememberAsyncImagePainter(gameDetail.imageUrl),
                        contentDescription = gameDetail.title,
                        contentScale = ContentScale.Crop,
                        modifier = Modifier.matchParentSize()
                    )

                    val currentIsFavorite = remember(viewModel.favoriteGameId, gameId) {
                        viewModel.favoriteGameId == gameId
                    }
                    val canToggleFavorite = bearer != null && userId != null
                    val currentStatus = userGame?.status ?: "No seguido"
                    val canFavorite = currentStatus.equals("Jugando", true) || currentStatus.equals("Completado", true)

                    Surface(
                        modifier = Modifier
                            .align(Alignment.TopEnd)
                            .padding(12.dp),
                        shape = CircleShape,
                        tonalElevation = 2.dp,
                        shadowElevation = 4.dp,
                        color = MaterialTheme.colorScheme.surface.copy(alpha = 0.85f)
                    ) {
                        IconButton(
                            onClick = {
                                if (!canToggleFavorite) {
                                    Toast.makeText(context, "Inicia sesión para marcar favorito", Toast.LENGTH_SHORT).show()
                                } else if (!canFavorite) {
                                    Toast.makeText(context, "Solo puedes marcar favorito si estás Jugando o Completado", Toast.LENGTH_LONG).show()
                                } else {
                                    viewModel.setFavorite(
                                        userId!!,
                                        bearer!!,
                                        gameId
                                    )
                                }
                            },
                            enabled = canToggleFavorite && !viewModel.isTogglingFavorite
                        ) {
                            val icon = if (currentIsFavorite) Icons.Filled.Star else Icons.Outlined.Star
                            val golden = Color(0xFFFFD700) // amarillo oro
                            val tint = if (currentIsFavorite) golden else MaterialTheme.colorScheme.onSurfaceVariant

                            Icon(
                                imageVector = icon,
                                contentDescription = if (currentIsFavorite) "Favorito actual" else "Marcar como favorito",
                                tint = tint,
                                modifier = Modifier.size(26.dp)
                            )
                        }
                    }
                }

                Spacer(Modifier.height(8.dp))

                Text(
                    text = gameDetail.title,
                    style = MaterialTheme.typography.headlineLarge,
                    color = MaterialTheme.colorScheme.onBackground,
                    modifier = Modifier
                        .align(Alignment.CenterHorizontally)
                        .padding(horizontal = 16.dp, vertical = 4.dp)
                )
                Text(
                    text = formatDate(gameDetail.releaseDate),
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.align(Alignment.CenterHorizontally)
                )
                Spacer(Modifier.height(16.dp))

                // -------- Selector de estado del juego --------
                val statusOptions = listOf("No seguido", "Por jugar", "Jugando", "Completado")
                val currentStatus = userGame?.status ?: "No seguido"
                val canReview = remember(currentStatus) {
                    currentStatus.equals("Completado", ignoreCase = true) ||
                            currentStatus.equals("Jugando", ignoreCase = true)
                }
                val canUpdate = userId != null

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    statusOptions.forEach { status ->
                        val isSelected = currentStatus == status
                        Button(
                            onClick = {
                                if (status == "No seguido" && currentStatus != "No seguido") {
                                    pendingStatus = status
                                    showConfirmRemove = true
                                } else {
                                    userId?.let { uid ->
                                        viewModel.updateGameStatus(uid, gameId, status)
                                    }
                                }
                            },
                            enabled = canUpdate,
                            modifier = Modifier
                                .weight(1f)
                                .padding(horizontal = 2.dp),
                            contentPadding = PaddingValues(4.dp),
                            shape = RoundedCornerShape(0.dp),
                            colors = ButtonDefaults.buttonColors(
                                containerColor = if (isSelected) MaterialTheme.colorScheme.primary
                                else MaterialTheme.colorScheme.surfaceVariant,
                                contentColor = if (isSelected) Color.White
                                else MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        ) { Text(status, fontSize = 12.sp) }
                    }
                }

                Spacer(Modifier.height(16.dp))

                // -------- Diálogo eliminación biblioteca --------
                if (showConfirmRemove) {
                    AlertDialog(
                        onDismissRequest = {
                            showConfirmRemove = false
                            pendingStatus = null
                        },
                        modifier = Modifier.fillMaxWidth(0.96f),
                        properties = DialogProperties(usePlatformDefaultWidth = false),
                        shape = RoundedCornerShape(20.dp),
                        title = { Text("Eliminar de tu biblioteca") },
                        text = {
                            Text(
                                buildAnnotatedString {
                                    append("¿Seguro que quieres eliminar el juego de tu biblioteca?\n\n")
                                    withStyle(style = SpanStyle(fontWeight = FontWeight.Bold)) {
                                        append("Esto eliminará tu reseña sobre el juego.")
                                    }
                                }
                            )
                        },
                        dismissButton = {
                            TextButton(
                                onClick = {
                                    showConfirmRemove = false
                                    pendingStatus = null
                                }
                            ) { Text("Cancelar") }
                        },
                        confirmButton = {
                            Button(
                                onClick = {
                                    val uid = userId
                                    if (uid != null) {
                                        viewModel.updateGameStatus(uid, gameId, "No seguido")
                                        bearer?.let { b -> viewModel.loadReviews(gameId, b) }
                                        Toast.makeText(
                                            context,
                                            "Juego eliminado de tu biblioteca",
                                            Toast.LENGTH_SHORT
                                        ).show()
                                    }
                                    showConfirmRemove = false
                                    pendingStatus = null
                                },
                                shape = RoundedCornerShape(12.dp),
                                colors = ButtonDefaults.buttonColors(
                                    containerColor = MaterialTheme.colorScheme.error,
                                    contentColor = MaterialTheme.colorScheme.onError
                                ),
                                contentPadding = PaddingValues(horizontal = 20.dp, vertical = 10.dp)
                            ) { Text("Sí, eliminar") }
                        }
                    )
                }

                // ----- Plataformas -----
                HorizontalDivider(
                    modifier = Modifier.padding(vertical = 8.dp, horizontal = 16.dp),
                    thickness = 1.dp,
                    color = MaterialTheme.colorScheme.primary,
                )
                Text(
                    text = "Plataformas",
                    style = MaterialTheme.typography.titleMedium,
                    modifier = Modifier
                        .align(Alignment.CenterHorizontally)
                        .padding(horizontal = 4.dp, vertical = 10.dp),
                )
                PlatformsSection(gameDetail.platforms)

                // ----- Géneros -----
                Text(
                    text = "Géneros",
                    style = MaterialTheme.typography.titleMedium,
                    modifier = Modifier
                        .align(Alignment.CenterHorizontally)
                        .padding(horizontal = 8.dp, vertical = 10.dp),
                )
                GenresSection(gameDetail.genres)

                // -------- Descripción --------
                HorizontalDivider(
                    modifier = Modifier.padding(vertical = 16.dp, horizontal = 16.dp),
                    thickness = 1.dp,
                    color = MaterialTheme.colorScheme.primary,
                )
                Text(
                    text = "Descripción",
                    style = MaterialTheme.typography.titleMedium,
                    modifier = Modifier
                        .align(Alignment.CenterHorizontally)
                        .padding(horizontal = 16.dp, vertical = 10.dp),
                )
                var expanded by remember { mutableStateOf(false) }
                Box(modifier = Modifier.padding(horizontal = 16.dp)) {
                    Text(
                        text = gameDetail.description ?: "Sin descripción.",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onBackground,
                        maxLines = if (expanded) Int.MAX_VALUE else 10,
                        overflow = TextOverflow.Clip
                    )
                    if (!expanded) {
                        Box(
                            modifier = Modifier
                                .matchParentSize()
                                .background(
                                    Brush.verticalGradient(
                                        colors = listOf(
                                            Color.Transparent,
                                            MaterialTheme.colorScheme.background
                                        ),
                                        startY = 60f,
                                        endY = Float.POSITIVE_INFINITY
                                    )
                                )
                        )
                    }
                }
                if (!gameDetail.description.isNullOrEmpty() && gameDetail.description.length > 200) {
                    TextButton(
                        onClick = { expanded = !expanded },
                        modifier = Modifier
                            .padding(horizontal = 16.dp)
                            .alpha(0.6f)
                            .align(Alignment.CenterHorizontally)
                    ) { Text(if (expanded) "Ver menos" else "Ver más", textDecoration = TextDecoration.Underline) }
                }

                Spacer(Modifier.height(16.dp))

                HorizontalDivider(
                    modifier = Modifier.padding(vertical = 16.dp, horizontal = 16.dp),
                    thickness = 1.dp,
                    color = MaterialTheme.colorScheme.primary,
                )

                // -------- Galería --------
                Text(
                    text = "Galería",
                    style = MaterialTheme.typography.titleMedium,
                    modifier = Modifier
                        .align(Alignment.CenterHorizontally)
                        .padding(horizontal = 16.dp, vertical = 10.dp),
                )
                LazyRow(
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                    modifier = Modifier.padding(horizontal = 16.dp)
                ) {
                    items(gameDetail.screenshots) { imageUrl ->
                        Image(
                            painter = rememberAsyncImagePainter(imageUrl),
                            contentDescription = null,
                            contentScale = ContentScale.FillHeight,
                            modifier = Modifier
                                .height(180.dp)
                                .widthIn(max = 400.dp)
                        )
                    }
                }

                Spacer(Modifier.height(16.dp))

                HorizontalDivider(
                    modifier = Modifier.padding(vertical = 16.dp, horizontal = 16.dp),
                    thickness = 1.dp,
                    color = MaterialTheme.colorScheme.primary,
                )

                // -------- Opiniones --------
                ReviewsSection(
                    title = "Opiniones",
                    reviews = viewModel.reviews,
                    isLoading = viewModel.isLoadingReviews,
                    error = viewModel.reviewsError
                )

                // -------- Tu reseña compacta --------
                if ((userGame?.score ?: 0) > 0 || !userGame?.notes.isNullOrBlank()) {
                    YourReviewCard(
                        score0to100 = userGame?.score ?: 0,
                        notes = userGame?.notes.orEmpty()
                    )
                    Spacer(Modifier.height(12.dp))
                }

                // -------- CTA reseña --------
                var showReviewSheet by remember { mutableStateOf(false) }
                Button(
                    onClick = {
                        when {
                            userId == null -> {
                                Toast.makeText(context, "Inicia sesión para reseñar", Toast.LENGTH_SHORT).show()
                            }
                            !canReview -> {
                                Toast.makeText(
                                    context,
                                    "Solo puedes reseñar si estás jugando o has completado el juego.",
                                    Toast.LENGTH_LONG
                                ).show()
                            }
                            else -> {
                                showReviewSheet = true
                            }
                        }
                    },
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 16.dp)
                ) {
                    Text(
                        if ((userGame?.score ?: 0) > 0 || !userGame?.notes.isNullOrBlank())
                            "Editar reseña"
                        else
                            "Escribir reseña"
                    )
                }

                Spacer(Modifier.height(24.dp))

                // -------- Hoja de reseña --------
                if (showReviewSheet) {
                    var tempScore100 by rememberSaveable { mutableStateOf(userGame?.score ?: 0) }
                    var tempNotes by rememberSaveable { mutableStateOf(userGame?.notes ?: "") }
                    var isSaving by remember { mutableStateOf(false) }
                    var errorMsg by remember { mutableStateOf<String?>(null) }

                    @OptIn(ExperimentalMaterial3Api::class)
                    ModalBottomSheet(
                        onDismissRequest = { if (!isSaving) showReviewSheet = false },
                        dragHandle = null
                    ) {
                        Column(
                            Modifier
                                .fillMaxWidth()
                                .padding(16.dp),
                            verticalArrangement = Arrangement.spacedBy(12.dp)
                        ) {
                            Text("Tu reseña", style = MaterialTheme.typography.titleLarge)

                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Text("Puntuación", style = MaterialTheme.typography.labelLarge)
                                Text(String.format("%.1f / 10", tempScore100 / 10f))
                            }

                            Slider(
                                value = tempScore100.toFloat(),
                                onValueChange = { tempScore100 = it.roundToInt().coerceIn(0, 100) },
                                valueRange = 0f..100f,
                                steps = 99
                            )

                            FiveStarRating(
                                score0to10 = tempScore100 / 10f,
                                starSize = 22.dp
                            )

                            OutlinedTextField(
                                value = tempNotes,
                                onValueChange = { tempNotes = it },
                                label = { Text("Escribe tu opinión") },
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .heightIn(min = 120.dp),
                                maxLines = 6
                            )

                            errorMsg?.let { Text(it, color = MaterialTheme.colorScheme.error) }

                            Row(
                                Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.End
                            ) {
                                TextButton(
                                    onClick = { if (!isSaving) showReviewSheet = false },
                                    enabled = !isSaving
                                ) { Text("Cancelar") }

                                Spacer(Modifier.width(8.dp))

                                Button(
                                    onClick = {
                                        isSaving = true
                                        errorMsg = null
                                        scope.launch {
                                            try {
                                                val b = bearer ?: error("Debes iniciar sesión")
                                                val score0to10Float = tempScore100 / 10f
                                                reviewsRepo.upsert(
                                                    gameId = gameId,
                                                    score0to10 = score0to10Float,
                                                    notes = tempNotes,
                                                    bearer = b
                                                ).getOrThrow()

                                                viewModel.loadReviews(gameId, b)
                                                userId?.let { uid -> viewModel.getUserGame(uid, gameId) }

                                                Toast.makeText(context, "Reseña guardada", Toast.LENGTH_SHORT).show()
                                                showReviewSheet = false
                                                userId?.let { uid -> viewModel.getUserGame(uid, gameId) }
                                            } catch (e: Exception) {
                                                errorMsg = e.message ?: "Error desconocido"
                                            } finally {
                                                isSaving = false
                                            }
                                        }
                                    },
                                    enabled = !isSaving
                                ) {
                                    if (isSaving) {
                                        CircularProgressIndicator(
                                            Modifier.size(18.dp),
                                            strokeWidth = 2.dp
                                        )
                                        Spacer(Modifier.width(8.dp))
                                    }
                                    Text("Guardar")
                                }
                            }

                            Spacer(Modifier.windowInsetsBottomHeight(WindowInsets.navigationBars))
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun YourReviewCard(
    score0to100: Int,
    notes: String,
    modifier: Modifier = Modifier
) {
    val surface = MaterialTheme.colorScheme.surface
    val overlay = MaterialTheme.colorScheme.primary.copy(alpha = 0.06f)

    Surface(
        modifier = modifier
            .padding(horizontal = 16.dp)
            .fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        tonalElevation = 3.dp,
        shadowElevation = 6.dp
    ) {
        Column(
            Modifier
                .background(Brush.verticalGradient(listOf(surface, overlay, surface)))
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            Row(
                Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text("Tu reseña", style = MaterialTheme.typography.titleMedium)
                FiveStarRating(score0to10 = (score0to100 / 10f), starSize = 16.dp)
            }
            if (notes.isNotBlank()) {
                Text(notes, style = MaterialTheme.typography.bodyMedium, lineHeight = 18.sp)
            } else {
                Text(
                    "Sin comentario.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    }
}

@Composable
fun FiveStarRating(
    score0to10: Float,
    modifier: Modifier = Modifier,
    starSize: Dp = 20.dp,
    tint: Color = MaterialTheme.colorScheme.primary
) {
    val raw5 = (score0to10 / 2f).coerceIn(0f, 5f)
    val q5 = (raw5 * 2f).roundToInt() / 2f

    Row(modifier = modifier) {
        repeat(5) { i ->
            val idx = i + 1
            val full = q5 >= idx
            val half = !full && q5 >= idx - 0.5f

            val icon = when {
                full -> Icons.Filled.Star
                half -> Icons.Filled.StarHalf
                else -> Icons.Outlined.Star
            }
            val starTint = if (full || half) tint else MaterialTheme.colorScheme.onSurfaceVariant

            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = starTint,
                modifier = Modifier.size(starSize)
            )
        }
    }
}

@OptIn(ExperimentalFoundationApi::class)
@Composable
fun ReviewsSection(
    title: String,
    reviews: List<Review>,
    isLoading: Boolean,
    error: String?
) {
    val displayReviews = remember(reviews) {
        reviews.filter { review ->
            val hasText = !review.notes.isNullOrBlank()
            val score = review.score0to10?.toFloat() ?: 0f
            val hasScore = score > 0f
            hasText || hasScore
        }
    }

    Column(Modifier.fillMaxWidth()) {
        Text(
            text = title,
            style = MaterialTheme.typography.titleMedium,
            modifier = Modifier
                .padding(horizontal = 16.dp)
                .align(Alignment.CenterHorizontally)
        )

        Spacer(modifier = Modifier.height(10.dp))

        when {
            isLoading -> {
                Box(
                    Modifier
                        .fillMaxWidth()
                        .height(160.dp),
                    contentAlignment = Alignment.Center
                ) { CircularProgressIndicator() }
            }
            error != null -> {
                Text(
                    "Error: $error",
                    color = MaterialTheme.colorScheme.error,
                    modifier = Modifier.padding(horizontal = 16.dp)
                )
            }
            displayReviews.isEmpty() -> {
                Text(
                    "Aún no hay reseñas. ¡Sé el primero!",
                    modifier = Modifier.padding(horizontal = 16.dp)
                )
            }
            else -> {
                ReviewsCarousel(displayReviews)
            }
        }
    }
}

@OptIn(ExperimentalFoundationApi::class)
@Composable
private fun ReviewsCarousel(reviews: List<Review>) {
    if (reviews.isEmpty()) return

    val CARD_HEIGHT = 200.dp
    var openReview by remember { mutableStateOf<Review?>(null) }

    val size = reviews.size
    val pagerState = rememberPagerState(initialPage = 0, pageCount = { size })

    LaunchedEffect(size) {
        if (pagerState.currentPage >= size) pagerState.scrollToPage(0)
    }
    LaunchedEffect(size) {
        if (size == 0) return@LaunchedEffect
        while (true) {
            kotlinx.coroutines.delay(3500)
            if (!pagerState.isScrollInProgress && size > 0) {
                val next = (pagerState.currentPage + 1) % size
                pagerState.animateScrollToPage(next)
            }
        }
    }

    Column {
        Box(
            Modifier
                .fillMaxWidth()
                .height(CARD_HEIGHT)
        ) {
            HorizontalPager(
                state = pagerState,
                pageSpacing = 12.dp,
                modifier = Modifier.matchParentSize()
            ) { page ->
                reviews.getOrNull(page)?.let { review ->
                    ReviewCard(
                        review = review,
                        modifier = Modifier
                            .padding(horizontal = 16.dp)
                            .fillMaxWidth()
                            .height(CARD_HEIGHT),
                        onClick = { openReview = review }
                    )
                }
            }
        }

        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(top = 8.dp),
            horizontalArrangement = Arrangement.Center
        ) {
            repeat(size) { i ->
                val selected = i == (pagerState.currentPage % size)
                Box(
                    Modifier
                        .padding(horizontal = 3.dp)
                        .size(if (selected) 9.dp else 7.dp)
                        .clip(CircleShape)
                        .background(
                            if (selected) MaterialTheme.colorScheme.primary
                            else MaterialTheme.colorScheme.outlineVariant
                        )
                )
            }
        }
        Spacer(Modifier.height(8.dp))
    }

    openReview?.let { r ->
        ReviewDialog(
            review = r,
            onDismiss = { openReview = null }
        )
    }
}

@Composable
private fun ReviewCard(
    review: Review,
    modifier: Modifier = Modifier,
    onClick: () -> Unit
) {
    val surface = MaterialTheme.colorScheme.surface
    val overlay = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.25f)

    Surface(
        modifier = modifier
            .clip(RoundedCornerShape(16.dp))
            .clickable(onClick = onClick),
        shape = RoundedCornerShape(16.dp),
        tonalElevation = 2.dp,
        shadowElevation = 4.dp
    ) {
        Column(
            Modifier
                .fillMaxSize()
                .background(Brush.verticalGradient(listOf(surface, overlay, surface)))
                .padding(16.dp)
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.SpaceBetween,
                modifier = Modifier.fillMaxWidth()
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    val avatarPainter = rememberAsyncImagePainter(
                        model = review.avatarUrl?.takeIf { it.isNotBlank() } ?: R.drawable.default_avatar
                    )
                    Image(
                        painter = avatarPainter,
                        contentDescription = "Avatar de ${review.username ?: "usuario"}",
                        modifier = Modifier
                            .size(40.dp)
                            .clip(CircleShape),
                        contentScale = ContentScale.Crop
                    )
                    Spacer(Modifier.width(12.dp))
                    Text(
                        review.username ?: "Usuario",
                        style = MaterialTheme.typography.titleMedium,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis
                    )
                }

                FiveStarRating(
                    score0to10 = (review.score0to10 ?: 0).toFloat(),
                    starSize = 18.dp,
                    tint = MaterialTheme.colorScheme.primary
                )
            }

            HorizontalDivider(
                modifier = Modifier.padding(vertical = 12.dp),
                thickness = 1.dp,
                color = MaterialTheme.colorScheme.outlineVariant
            )

            Text(
                text = review.notes?.ifBlank { "Sin comentario." } ?: "Sin comentario.",
                style = MaterialTheme.typography.bodyMedium,
                lineHeight = 18.sp,
                maxLines = 6,
                overflow = TextOverflow.Ellipsis,
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f)
            )
        }
    }
}

@Composable
private fun ReviewDialog(
    review: Review,
    onDismiss: () -> Unit
) {
    Dialog(
        onDismissRequest = onDismiss,
        properties = DialogProperties(usePlatformDefaultWidth = false)
    ) {
        Surface(
            shape = RoundedCornerShape(20.dp),
            tonalElevation = 6.dp,
            shadowElevation = 8.dp,
            color = MaterialTheme.colorScheme.surface,
            modifier = Modifier
                .fillMaxWidth(0.96f)
        ) {
            Column(
                Modifier
                    .padding(16.dp)
                    .verticalScroll(rememberScrollState()),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.SpaceBetween,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        val avatarPainter = rememberAsyncImagePainter(
                            model = review.avatarUrl?.takeIf { it.isNotBlank() } ?: R.drawable.default_avatar
                        )
                        Image(
                            painter = avatarPainter,
                            contentDescription = "Avatar de ${review.username ?: "usuario"}",
                            modifier = Modifier
                                .size(44.dp)
                                .clip(CircleShape),
                            contentScale = ContentScale.Crop
                        )
                        Spacer(Modifier.width(12.dp))
                        Text(
                            review.username ?: "Usuario",
                            style = MaterialTheme.typography.titleLarge
                        )
                    }

                    FiveStarRating(
                        score0to10 = (review.score0to10 ?: 0).toFloat(),
                        starSize = 20.dp,
                        tint = MaterialTheme.colorScheme.primary
                    )
                }

                HorizontalDivider(
                    modifier = Modifier.padding(vertical = 4.dp),
                    thickness = 1.dp,
                    color = MaterialTheme.colorScheme.outlineVariant
                )

                Text(
                    text = review.notes?.ifBlank { "Sin comentario." } ?: "Sin comentario.",
                    style = MaterialTheme.typography.bodyLarge,
                    lineHeight = 20.sp
                )

                Row(
                    Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.End
                ) {
                    TextButton(onClick = onDismiss) { Text("Cerrar") }
                }
            }
        }
    }
}
