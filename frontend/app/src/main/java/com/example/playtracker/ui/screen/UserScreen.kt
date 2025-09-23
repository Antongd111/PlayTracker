@file:OptIn(ExperimentalMaterial3Api::class)

package com.example.playtracker.ui.screen

import android.widget.Toast
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Edit
import androidx.compose.material.icons.filled.PersonAdd
import androidx.compose.material.icons.filled.Star
import androidx.compose.material.icons.outlined.Star
import androidx.compose.material3.*
import androidx.compose.material3.SegmentedButton
import androidx.compose.material3.SegmentedButtonDefaults
import androidx.compose.material3.SingleChoiceSegmentedButtonRow
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavController
import coil.compose.rememberAsyncImagePainter
import com.example.playtracker.R
import com.example.playtracker.data.local.datastore.UserPreferences
import com.example.playtracker.domain.model.Friend
import com.example.playtracker.domain.model.UserGame
import com.example.playtracker.ui.viewmodel.*
import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.sp
import androidx.compose.material.icons.automirrored.filled.ExitToApp
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import kotlinx.coroutines.launch

@Composable
fun UserScreen(
    navController: NavController,
    innerNavController: NavController,
    userId: Int
) {
    val viewModel: UserViewModel = viewModel(key = "UserVM_$userId")

    val context = LocalContext.current
    val prefs = remember { UserPreferences(context) }
    val token by prefs.tokenFlow.collectAsState(initial = null)
    val bearer = token?.let { "Bearer $it" }

    val scroll = rememberScrollState()
    val ui by viewModel.ui.collectAsState()

    var showEditDialog by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()

    LaunchedEffect(userId, token) {
        viewModel.load(userId, token)
    }

    fun snack(msg: String) = Toast.makeText(context, msg, Toast.LENGTH_SHORT).show()

    when {
        ui.loading && ui.user == null -> Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            CircularProgressIndicator()
        }
        ui.error != null && ui.user == null -> Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            Text(ui.error ?: "Error")
        }
        ui.user != null -> {
            val u = ui.user!!

            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .background(MaterialTheme.colorScheme.background)
            ) {
                Column(modifier = Modifier.fillMaxSize()) {

                    // ===== Header =====
                    val avatarSize = 100.dp
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        modifier = Modifier
                            .fillMaxWidth()
                            .background(MaterialTheme.colorScheme.surface)
                            .heightIn(min = avatarSize + 20.dp)
                            .padding(horizontal = 10.dp)
                            .padding(top = 20.dp, bottom = 10.dp)
                    ) {
                        val avatarPainter = rememberAsyncImagePainter(
                            model = u.avatarUrl?.takeIf { it.isNotBlank() } ?: R.drawable.default_avatar
                        )
                        Image(
                            painter = avatarPainter,
                            contentDescription = "Avatar",
                            modifier = Modifier
                                .size(avatarSize)
                                .clip(CircleShape),
                            contentScale = ContentScale.Crop
                        )

                        Spacer(Modifier.width(20.dp))

                        Column(Modifier.weight(1f)) {
                            Text(u.name, style = MaterialTheme.typography.titleLarge)
                            Spacer(Modifier.height(6.dp))
                            u.status?.let { Text(it, style = MaterialTheme.typography.bodyMedium) }
                        }

                        if (ui.isOwn) {
                            Row {
                                // Editar perfil
                                IconButton(onClick = { showEditDialog = true }) {
                                    Icon(Icons.Default.Edit, contentDescription = "Editar perfil")
                                }
                                // Cerrar sesión
                                IconButton(
                                    onClick = {
                                        scope.launch {
                                            // Limpia credenciales (token, userId, etc.)
                                            prefs.clear()

                                            // Mensaje opcional
                                            Toast.makeText(context, "Sesión cerrada", Toast.LENGTH_SHORT).show()

                                            // Navega a login y limpia el back stack del shell principal
                                            navController.navigate("login") {
                                                popUpTo("main") { inclusive = true }
                                                launchSingleTop = true
                                            }
                                        }
                                    }
                                ) {
                                    Icon(
                                        imageVector = Icons.AutoMirrored.Filled.ExitToApp,
                                        contentDescription = "Cerrar sesión"
                                    )
                                }
                            }
                        }
                    }

                    // ===== Acciones amistad =====
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        modifier = Modifier
                            .fillMaxWidth()
                            .background(MaterialTheme.colorScheme.surface)
                            .padding(bottom = 10.dp, end = 10.dp, start = 10.dp)
                    ) {
                        Spacer(modifier = Modifier.weight(1f))

                        if (!ui.isOwn) {
                            val (label, enabled) = when (ui.friendState) {
                                FriendState.NONE -> "Seguir" to !ui.workingFriend
                                FriendState.PENDING_SENT -> "Pendiente..." to !ui.workingFriend
                                FriendState.FRIENDS -> "Amigos ✓" to !ui.workingFriend
                            }
                            Button(
                                onClick = {
                                    val b = bearer ?: return@Button snack("Necesitas iniciar sesión")
                                    viewModel.toggleFriendAction(b)
                                },
                                enabled = enabled
                            ) {
                                Icon(
                                    imageVector = Icons.Default.PersonAdd,
                                    contentDescription = label,
                                    tint = MaterialTheme.colorScheme.onPrimary
                                )
                                Spacer(Modifier.width(8.dp))
                                Text(label)
                            }
                        }
                    }

                    // ===== Cuerpo scroll =====
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(top = 15.dp, bottom = 16.dp, start = 10.dp, end = 10.dp)
                            .verticalScroll(scroll)
                            .weight(1f)
                    ) {
                        // --- Favorito ---
                        Text("Juego favorito", style = MaterialTheme.typography.titleMedium)

                        when {
                            ui.favorite == null -> {
                                Card(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .padding(vertical = 8.dp),
                                    shape = RoundedCornerShape(12.dp),
                                    colors = CardDefaults.cardColors(
                                        containerColor = MaterialTheme.colorScheme.surface
                                    ),
                                ) {
                                    Box(
                                        modifier = Modifier
                                            .fillMaxWidth()
                                            .heightIn(min = 100.dp)
                                            .padding(12.dp),
                                        contentAlignment = Alignment.Center
                                    ) {
                                        Column(
                                            modifier = Modifier.fillMaxWidth(),
                                            horizontalAlignment = Alignment.CenterHorizontally
                                        ) {
                                            Text(
                                                "— sin favorito —",
                                                style = MaterialTheme.typography.bodyLarge,
                                                textAlign = TextAlign.Center,
                                                modifier = Modifier.fillMaxWidth()
                                            )
                                            Spacer(Modifier.height(4.dp))
                                            Text(
                                                "Elige un juego y márcalo con la ⭐",
                                                style = MaterialTheme.typography.labelSmall,
                                                textAlign = TextAlign.Center,
                                                modifier = Modifier.fillMaxWidth()
                                            )
                                        }
                                    }
                                }
                            }
                            else -> {
                                val fav = ui.favorite!!
                                Card(
                                    onClick = { navController.navigate("gameDetail/${fav.gameRawgId}") },
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .padding(vertical = 8.dp),
                                    shape = RoundedCornerShape(12.dp),
                                    colors = CardDefaults.cardColors(
                                        containerColor = MaterialTheme.colorScheme.surface
                                    ),
                                ) {
                                    Row(
                                        modifier = Modifier
                                            .fillMaxWidth()
                                            .height(120.dp)
                                    ) {
                                        val img = fav.imageUrl
                                        Image(
                                            painter = rememberAsyncImagePainter(
                                                model = img?.takeIf { it.isNotBlank() } ?: R.drawable.default_avatar
                                            ),
                                            contentDescription = null,
                                            contentScale = ContentScale.Crop,
                                            modifier = Modifier
                                                .fillMaxHeight()
                                                .aspectRatio(1f) // cuadrada; quítalo si prefieres un rectángulo
                                                .clip(RoundedCornerShape(topStart = 12.dp, bottomStart = 12.dp))
                                        )

                                        // Contenido a la derecha
                                        Column(
                                            modifier = Modifier
                                                .weight(1f)
                                                .fillMaxHeight()
                                                .padding(horizontal = 12.dp, vertical = 10.dp),
                                            verticalArrangement = Arrangement.SpaceBetween
                                        ) {
                                            Column {
                                                Text(
                                                    fav.gameTitle ?: "Juego",
                                                    style = MaterialTheme.typography.titleMedium,
                                                    maxLines = 1,
                                                    overflow = TextOverflow.Ellipsis
                                                )
                                                Spacer(Modifier.height(6.dp))
                                                StarRowFrom100(score100 = fav.score, size = 16.dp)
                                            }
                                            Text(
                                                "Ver detalles",
                                                style = MaterialTheme.typography.labelSmall,
                                                color = MaterialTheme.colorScheme.primary
                                            )
                                        }
                                    }
                                }
                            }
                        }

                        HorizontalDivider(
                            modifier = Modifier.padding(vertical = 16.dp),
                            thickness = 1.dp,
                            color = MaterialTheme.colorScheme.primary
                        )

                        // --- Selector de estado + lista ---
                        val statusOptions = listOf("Por jugar", "Jugando", "Completado")
                        var selectedIndex by rememberSaveable { mutableStateOf(2) } // por defecto "Completado"
                        val selectedStatus = statusOptions[selectedIndex]
                        val filteredCount = remember(ui.userGames, selectedStatus) {
                            ui.userGames.count { it.status?.equals(selectedStatus, ignoreCase = true) == true }
                        }

                        Text("Juegos ($selectedStatus) ($filteredCount)", style = MaterialTheme.typography.titleMedium)
                        Spacer(Modifier.height(8.dp))

                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(vertical = 8.dp),
                            horizontalArrangement = Arrangement.Center
                        ) {
                            SingleChoiceSegmentedButtonRow {
                                statusOptions.forEachIndexed { index, label ->
                                    SegmentedButton(
                                        selected = selectedIndex == index,
                                        onClick = { selectedIndex = index },
                                        shape = SegmentedButtonDefaults.itemShape(index, statusOptions.size),
                                        colors = SegmentedButtonDefaults.colors(
                                            activeContainerColor = MaterialTheme.colorScheme.primary,
                                            activeContentColor = MaterialTheme.colorScheme.onPrimary,
                                            inactiveContainerColor = MaterialTheme.colorScheme.surface,
                                            inactiveContentColor = MaterialTheme.colorScheme.onSurface
                                        ),
                                        icon = {}
                                    ) {
                                        Text(label, style = MaterialTheme.typography.labelSmall, maxLines = 1)
                                    }
                                }
                            }
                        }

                        val filteredUG = remember(ui.userGames, selectedStatus) {
                            ui.userGames.filter { it.status?.equals(selectedStatus, ignoreCase = true) == true }
                        }

                        Spacer(Modifier.height(8.dp))

                        if (filteredUG.isEmpty()) {
                            val emptyMsg = when (selectedStatus) {
                                "Por jugar" -> "Aún no hay juegos por jugar."
                                "Jugando" -> "Aún no hay juegos en progreso."
                                else -> "Aún no hay juegos completados."
                            }
                            Text(
                                emptyMsg,
                                style = MaterialTheme.typography.bodyMedium,
                                modifier = Modifier.padding(vertical = 8.dp)
                            )
                        } else {
                            LazyRow(
                                horizontalArrangement = Arrangement.spacedBy(12.dp),
                                modifier = Modifier.padding(vertical = 8.dp)
                            ) {
                                items(filteredUG, key = { it.id }) { ug: UserGame ->
                                    Card(
                                        onClick = { navController.navigate("gameDetail/${ug.gameRawgId}") },
                                        modifier = Modifier
                                            .width(160.dp)
                                            .wrapContentHeight(),
                                        shape = RoundedCornerShape(12.dp),
                                        colors = CardDefaults.cardColors(
                                            containerColor = MaterialTheme.colorScheme.surface
                                        ),
                                        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
                                    ) {
                                        Column(Modifier.fillMaxWidth()) {
                                            val img = ug.imageUrl
                                            Image(
                                                painter = rememberAsyncImagePainter(
                                                    model = img?.takeIf { it.isNotBlank() } ?: R.drawable.default_avatar
                                                ),
                                                contentDescription = null,
                                                contentScale = ContentScale.Crop,
                                                modifier = Modifier
                                                    .fillMaxWidth()
                                                    .height(120.dp)
                                                    .clip(RoundedCornerShape(topStart = 12.dp, topEnd = 12.dp))
                                            )

                                            Spacer(Modifier.height(8.dp))

                                            Text(
                                                ug.gameTitle ?: "Juego",
                                                style = MaterialTheme.typography.bodySmall,
                                                modifier = Modifier
                                                    .fillMaxWidth()
                                                    .padding(horizontal = 8.dp),
                                                maxLines = 1,
                                                textAlign = TextAlign.Center
                                            )

                                            Spacer(Modifier.height(4.dp))

                                            Row(
                                                horizontalArrangement = Arrangement.Center,
                                                modifier = Modifier
                                                    .fillMaxWidth()
                                                    .padding(bottom = 8.dp)
                                            ) {
                                                StarRowFrom100(score100 = ug.score, size = 14.dp)
                                            }
                                        }
                                    }
                                }
                            }
                        }

                        HorizontalDivider(
                            modifier = Modifier.padding(vertical = 16.dp),
                            thickness = 1.dp,
                            color = MaterialTheme.colorScheme.primary
                        )

                        // --- Reseñas en carrusel ---
                        UserReviewsSection(
                            reviews = ui.reviews,
                            navController = navController
                        )

                        HorizontalDivider(
                            modifier = Modifier.padding(vertical = 16.dp),
                            thickness = 1.dp,
                            color = MaterialTheme.colorScheme.primary
                        )

                        // --- Amigos ---
                        Text("Amigos", style = MaterialTheme.typography.titleMedium)

                        if (ui.friends.isEmpty()) {
                            Text(
                                "Aún no tiene amigos.",
                                style = MaterialTheme.typography.bodyMedium,
                                modifier = Modifier.padding(vertical = 8.dp)
                            )
                        } else {
                            LazyRow(
                                horizontalArrangement = Arrangement.spacedBy(16.dp),
                                modifier = Modifier.padding(top = 12.dp)
                            ) {
                                items(ui.friends, key = { it.id }) { friend: Friend ->
                                    Card(
                                        onClick = { innerNavController.navigate("user/${friend.id}") },
                                        shape = RoundedCornerShape(12.dp),
                                        colors = CardDefaults.cardColors(
                                            containerColor = MaterialTheme.colorScheme.surface
                                        ),
                                        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
                                        modifier = Modifier
                                            .width(120.dp)
                                            .wrapContentHeight()
                                    ) {
                                        Column(
                                            horizontalAlignment = Alignment.CenterHorizontally,
                                            modifier = Modifier.padding(12.dp)
                                        ) {
                                            val avatar = rememberAsyncImagePainter(
                                                model = friend.avatarUrl?.takeIf { it.isNotBlank() } ?: R.drawable.default_avatar
                                            )
                                            Image(
                                                painter = avatar,
                                                contentDescription = "Avatar de ${friend.name}",
                                                modifier = Modifier
                                                    .size(72.dp)
                                                    .clip(CircleShape),
                                                contentScale = ContentScale.Crop
                                            )
                                            Spacer(Modifier.height(8.dp))
                                            Text(
                                                friend.name,
                                                style = MaterialTheme.typography.bodySmall,
                                                maxLines = 1,
                                                textAlign = TextAlign.Center,
                                                modifier = Modifier.fillMaxWidth()
                                            )
                                        }
                                    }
                                }
                            }
                        }

                        Spacer(Modifier.height(30.dp))
                    }
                }

                if (ui.isOwn) {
                    EditProfileDialog(
                        isOpen = showEditDialog,
                        initialName = u.name,
                        initialStatus = u.status,
                        onDismiss = { showEditDialog = false },
                        onSave = { newName, newStatus ->
                            val b = bearer ?: return@EditProfileDialog Toast
                                .makeText(context, "Necesitas iniciar sesión", Toast.LENGTH_SHORT)
                                .show()
                            viewModel.updateProfile(newName, newStatus, b)
                            showEditDialog = false
                            Toast.makeText(context, "Perfil actualizado", Toast.LENGTH_SHORT).show()
                        }
                    )
                }
            }
        }
    }
}

/* ====== Dialogo de edición ====== */
@Composable
private fun EditProfileDialog(
    isOpen: Boolean,
    initialName: String,
    initialStatus: String?,
    onDismiss: () -> Unit,
    onSave: (name: String, status: String?) -> Unit
) {
    if (!isOpen) return

    var name by remember(initialName) { mutableStateOf(initialName) }
    var status by remember(initialStatus) { mutableStateOf(initialStatus.orEmpty()) }
    var nameError by remember { mutableStateOf<String?>(null) }

    AlertDialog(
        onDismissRequest = onDismiss,
        confirmButton = {
            TextButton(onClick = {
                val n = name.trim()
                if (n.isEmpty()) {
                    nameError = "El nombre no puede estar vacío"
                    return@TextButton
                }
                onSave(n, status.trim().ifBlank { null })
            }) { Text("Guardar") }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancelar") } },
        title = { Text("Editar perfil") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                OutlinedTextField(
                    value = name,
                    onValueChange = {
                        name = it
                        if (nameError != null) nameError = null
                    },
                    label = { Text("Nombre de usuario") },
                    singleLine = true,
                    isError = nameError != null,
                    supportingText = { if (nameError != null) Text(nameError!!) }
                )
                OutlinedTextField(
                    value = status,
                    onValueChange = { status = it },
                    label = { Text("Estado (opcional)") },
                    singleLine = true
                )
            }
        },
        shape = MaterialTheme.shapes.extraLarge
    )
}

/* ====== Helper estrellas (0..100 -> 0..5) ====== */
@Composable
private fun StarRowFrom100(
    score100: Int?,
    maxStars: Int = 5,
    size: Dp = 16.dp
) {
    val s = (score100 ?: 0).coerceIn(0, 100)
    val stars = ((s + 10) / 20)

    Row(verticalAlignment = Alignment.CenterVertically) {
        repeat(maxStars) { i ->
            Icon(
                imageVector = if (i < stars) Icons.Filled.Star else Icons.Outlined.Star,
                contentDescription = null,
                tint = if (i < stars) MaterialTheme.colorScheme.primary
                else MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.size(size)
            )
        }
    }
}


@OptIn(ExperimentalFoundationApi::class)
@Composable
private fun UserReviewsSection(
    reviews: List<UserGame>,
    navController: NavController
) {
    val display = remember(reviews) {
        reviews.filter { !it.notes.isNullOrBlank() || (it.score ?: 0) > 0 }
    }

    Text(
        "Reseñas (${display.size})",
        style = MaterialTheme.typography.titleMedium
    )

    Spacer(Modifier.height(15.dp))

    when {
        display.isEmpty() -> {
            Text(
                "Aún no hay reseñas.",
                style = MaterialTheme.typography.bodyMedium,
                modifier = Modifier.padding(vertical = 8.dp)
            )
        }
        else -> {
            UserReviewsCarousel(display, navController)
        }
    }
}

@OptIn(ExperimentalFoundationApi::class)
@Composable
private fun UserReviewsCarousel(
    reviews: List<UserGame>,
    navController: NavController
) {
    val reviewHeight = 200.dp // altura fija del hueco de reseñas
    val pagerState = rememberPagerState(initialPage = 0, pageCount = { reviews.size })

    LaunchedEffect(reviews.size) {
        if (reviews.isEmpty()) return@LaunchedEffect
        while (true) {
            kotlinx.coroutines.delay(3500)
            if (!pagerState.isScrollInProgress) {
                val next = (pagerState.currentPage + 1) % reviews.size
                pagerState.animateScrollToPage(next)
            }
        }
    }

    Column {
        Box(
            Modifier
                .fillMaxWidth()
                .height(reviewHeight)
        ) {
            HorizontalPager(
                state = pagerState,
                pageSpacing = 12.dp,
                modifier = Modifier.matchParentSize()
            ) { page ->
                val ug = reviews.getOrNull(page) ?: return@HorizontalPager
                UserReviewCard(
                    ug = ug,
                    onClick = { navController.navigate("gameDetail/${ug.gameRawgId}") },
                    modifier = Modifier
                        .padding(horizontal = 16.dp)
                        .fillMaxWidth()
                        .height(reviewHeight)
                )
            }
        }

        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(top = 8.dp),
            horizontalArrangement = Arrangement.Center
        ) {
            repeat(reviews.size) { i ->
                val selected = i == (pagerState.currentPage % reviews.size)
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
}

@Composable
private fun UserReviewCard(
    ug: UserGame,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier.clickable(onClick = onClick),
        shape = RoundedCornerShape(16.dp),
        tonalElevation = 2.dp,
        shadowElevation = 4.dp
    ) {
        // Estructura en columna para fijar cabecera arriba y texto abajo
        Column(
            Modifier
                .fillMaxSize()
                .padding(12.dp)
        ) {
            // Cabecera: imagen izquierda, título derecha y debajo las estrellas
            Row(
                verticalAlignment = Alignment.Top,
                modifier = Modifier.fillMaxWidth()
            ) {
                Image(
                    painter = rememberAsyncImagePainter(ug.imageUrl ?: R.drawable.default_avatar),
                    contentDescription = ug.gameTitle,
                    modifier = Modifier
                        .size(56.dp)
                        .clip(RoundedCornerShape(8.dp)),
                    contentScale = ContentScale.Crop
                )

                Spacer(Modifier.width(12.dp))

                Column(
                    modifier = Modifier.weight(1f),
                    verticalArrangement = Arrangement.spacedBy(4.dp)
                ) {
                    Text(
                        ug.gameTitle ?: "Juego",
                        style = MaterialTheme.typography.titleMedium,
                        maxLines = 1
                    )
                    // Puntuación del usuario (estrellas desde 0..100)
                    StarRowFrom100(score100 = ug.score, size = 20.dp)
                }
            }

            HorizontalDivider(
                modifier = Modifier.padding(vertical = 16.dp),
                thickness = 1.dp,
                color = MaterialTheme.colorScheme.primary
            )

            // Texto de la reseña ocupando el resto del alto disponible
            Text(
                text = ug.notes.orEmpty(),
                style = MaterialTheme.typography.bodySmall.copy(fontSize = 14.sp),
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f),
                maxLines = 6,
                overflow = TextOverflow.Ellipsis
            )
        }
    }
}
