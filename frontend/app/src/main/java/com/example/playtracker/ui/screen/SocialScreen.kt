package com.example.playtracker.ui.screen

import android.widget.Toast
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Close
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavHostController
import coil.compose.rememberAsyncImagePainter
import com.example.playtracker.R
import com.example.playtracker.data.local.datastore.UserPreferences
import com.example.playtracker.data.remote.service.RetrofitInstance
import com.example.playtracker.domain.model.FriendRequest
import com.example.playtracker.domain.model.User
import com.example.playtracker.ui.components.SearchBar
import com.example.playtracker.ui.components.UserListItem
import com.example.playtracker.ui.viewmodel.FriendState
import com.example.playtracker.ui.viewmodel.SocialViewModel

@Composable
fun SocialScreen(
    navController: NavHostController
) {
    val viewModel: SocialViewModel = viewModel(key = "SocialVM")

    val context = LocalContext.current
    val prefs = remember { UserPreferences(context) }
    val token by prefs.tokenFlow.collectAsState(initial = null)
    val bearer = token?.let { "Bearer $it" }

    val ui by viewModel.ui.collectAsState()

    var search by remember { mutableStateOf("") }
    var showIncomingDialog by remember { mutableStateOf(false) }
    var myUserId by remember { mutableStateOf<Int?>(null) }

    fun snack(msg: String) = Toast.makeText(context, msg, Toast.LENGTH_SHORT).show()

    // 1) Cargar mi userId cuando haya bearer
    LaunchedEffect(bearer) {
        val b = bearer ?: run {
            myUserId = null
            return@LaunchedEffect
        }

        runCatching { RetrofitInstance.userApi.getCurrentUser(b) }
            .onSuccess { me ->
                myUserId = me.id
            }
            .onFailure { e ->
                myUserId = null
                snack("No se pudo cargar tu usuario: ${e.message ?: ""}")
            }
    }

    // 2) Cargar solicitudes entrantes cuando sepamos miUserId
    LaunchedEffect(bearer, myUserId) {
        val b = bearer ?: return@LaunchedEffect
        val meId = myUserId ?: return@LaunchedEffect
        viewModel.loadIncoming(bearer = b, myUserId = meId)
    }

    // 3) Hidratar estados cuando cambien los resultados (y tengamos bearer + miUserId)
    LaunchedEffect(bearer, myUserId, ui.results) {
        val b = bearer ?: return@LaunchedEffect
        val meId = myUserId ?: return@LaunchedEffect
        if (ui.results.isNotEmpty()) {
            viewModel.hydrateStatesForResults(bearer = b, myUserId = meId)
        }
    }

    Surface(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background),
        color = MaterialTheme.colorScheme.background
    ) {
        Column(Modifier.padding(16.dp)) {

            SearchBar(
                value = search,
                onValueChange = { search = it },
                onSearch = {
                    viewModel.search(search)

                    val b = bearer
                    val meId = myUserId
                    if (b != null && meId != null) {
                        viewModel.hydrateStatesForResults(bearer = b, myUserId = meId)
                    }
                }
            )

            Spacer(Modifier.height(12.dp))

            if (ui.incoming.isNotEmpty()) {
                IncomingRequestsBanner(
                    count = ui.incoming.size,
                    onClick = { showIncomingDialog = true }
                )
                Spacer(Modifier.height(12.dp))
            }

            if (ui.results.isEmpty()) {
                Box(
                    Modifier
                        .fillMaxSize()
                        .padding(top = 32.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = if (ui.isSearching) "No hay resultados" else "Busca cualquier persona...",
                        style = MaterialTheme.typography.bodyLarge,
                        color = MaterialTheme.colorScheme.onBackground
                    )
                }
            } else {
                LazyColumn(verticalArrangement = Arrangement.spacedBy(16.dp)) {
                    items(ui.results, key = { it.id }) { user: User ->
                        val isWorking = ui.workingFor.contains(user.id)
                        val state = ui.states[user.id] ?: FriendState.NONE

                        UserListItem(
                            user = user,
                            isWorking = isWorking,
                            state = state,
                            onMainButtonClick = {
                                val b = bearer ?: return@UserListItem
                                val meId = myUserId ?: return@UserListItem

                                viewModel.toggleFriendAction(
                                    userId = user.id,
                                    bearer = b,
                                    myUserId = meId,
                                    onSnack = ::snack
                                )
                            },
                            onClick = { navController.navigate("user/${user.id}") }
                        )
                    }
                }
            }
        }

        if (showIncomingDialog) {
            IncomingRequestsDialog(
                isOpen = showIncomingDialog,
                onDismiss = { showIncomingDialog = false },
                requests = ui.incoming,
                working = ui.workingIncoming,
                onAccept = onAccept@ { fromUserId ->
                    val b = bearer ?: return@onAccept
                    val meId = myUserId ?: return@onAccept
                    viewModel.acceptIncoming(fromUserId = fromUserId, bearer = b, myUserId = meId, onSnack = ::snack)
                },
                onDecline = onDecline@ { fromUserId ->
                    val b = bearer ?: return@onDecline
                    val meId = myUserId ?: return@onDecline
                    viewModel.declineIncoming(fromUserId = fromUserId, bearer = b, myUserId = meId, onSnack = ::snack)
                }
            )
        }
    }
}

/* ===================== UI helpers ===================== */

@Composable
private fun IncomingRequestsBanner(
    count: Int,
    onClick: () -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .heightIn(min = 56.dp)
            .clickable { onClick() },
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.secondaryContainer
        )
    ) {
        Row(
            Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 12.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Column(Modifier.weight(1f)) {
                Text(
                    text = "Solicitudes entrantes",
                    style = MaterialTheme.typography.titleMedium,
                    color = MaterialTheme.colorScheme.onSecondaryContainer
                )
                Text(
                    text = "Tienes $count pendientes",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSecondaryContainer
                )
            }
            FilledTonalButton(onClick = onClick) { Text("Ver") }
        }
    }
}

@Composable
private fun IncomingRequestsDialog(
    isOpen: Boolean,
    onDismiss: () -> Unit,
    requests: List<FriendRequest>,
    working: Set<Int>,
    onAccept: (fromUserId: Int) -> Unit,
    onDecline: (fromUserId: Int) -> Unit
) {
    if (!isOpen) return

    val config = LocalConfiguration.current
    val maxDialogHeight = config.screenHeightDp.dp * 0.8f

    Dialog(
        onDismissRequest = onDismiss,
        properties = DialogProperties(usePlatformDefaultWidth = false)
    ) {
        Surface(
            shape = MaterialTheme.shapes.extraLarge,
            tonalElevation = 6.dp,
            modifier = Modifier
                .fillMaxWidth(0.92f)
                .heightIn(max = maxDialogHeight)
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(20.dp)
            ) {
                Row(
                    Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text("Solicitudes entrantes", style = MaterialTheme.typography.titleLarge)
                    TextButton(onClick = onDismiss) { Text("Cerrar") }
                }

                Spacer(Modifier.height(12.dp))

                if (requests.isEmpty()) {
                    Text(
                        "No tienes solicitudes pendientes.",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                } else {
                    LazyColumn(
                        modifier = Modifier
                            .fillMaxWidth()
                            .weight(1f, fill = true),
                        verticalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        items(requests, key = { it.otherUser.id }) { req ->
                            val uid = req.otherUser.id
                            val isBusy = working.contains(uid)

                            val avatarPainter = rememberAsyncImagePainter(
                                model = req.otherUser.avatarUrl?.takeIf { it.isNotBlank() } ?: R.drawable.default_avatar
                            )

                            ElevatedCard(
                                modifier = Modifier.fillMaxWidth(),
                                colors = CardDefaults.elevatedCardColors(
                                    containerColor = MaterialTheme.colorScheme.background
                                )
                            ) {
                                Row(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .padding(horizontal = 14.dp, vertical = 12.dp),
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Image(
                                        painter = avatarPainter,
                                        contentDescription = "Avatar",
                                        modifier = Modifier
                                            .size(52.dp)
                                            .clip(CircleShape)
                                    )

                                    Spacer(Modifier.width(14.dp))

                                    Column(Modifier.weight(1f)) {
                                        Text(
                                            text = req.otherUser.name,
                                            style = MaterialTheme.typography.titleMedium
                                        )
                                        Text(
                                            text = "te ha enviado una solicitud",
                                            style = MaterialTheme.typography.bodySmall,
                                            color = MaterialTheme.colorScheme.onSurfaceVariant
                                        )
                                    }

                                    Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                                        IconButton(
                                            onClick = { onDecline(uid) },
                                            enabled = !isBusy
                                        ) {
                                            Icon(
                                                imageVector = Icons.Default.Close,
                                                contentDescription = "Rechazar",
                                                tint = MaterialTheme.colorScheme.error
                                            )
                                        }
                                        IconButton(
                                            onClick = { onAccept(uid) },
                                            enabled = !isBusy
                                        ) {
                                            Icon(
                                                imageVector = Icons.Default.Check,
                                                contentDescription = "Aceptar",
                                                tint = MaterialTheme.colorScheme.primary
                                            )
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
