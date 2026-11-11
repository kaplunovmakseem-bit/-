package ru.taskpriority.ui.zone

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Add
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import ru.taskpriority.R
import ru.taskpriority.ui.AppViewModelProvider
import ru.taskpriority.ui.components.SwipeToDeleteBox
import ru.taskpriority.ui.components.TaskCard
import ru.taskpriority.ui.components.rememberTaskActionHandlers
import ru.taskpriority.ui.theme.colors

/** Одна зона матрицы на весь экран: активные задачи, ниже — выполненные. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ZoneScreen(
    onBack: () -> Unit,
    onAddTask: () -> Unit,
    onEditTask: (Long) -> Unit,
    viewModel: ZoneViewModel = viewModel(factory = AppViewModelProvider.Factory),
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    val snackbarHostState = remember { SnackbarHostState() }
    val actions = rememberTaskActionHandlers(viewModel, snackbarHostState)
    val zoneColors = viewModel.zone.colors()

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        stringResource(R.string.zone_title_with_count, stringResource(viewModel.zone.titleRes), uiState.active.size),
                        fontWeight = FontWeight.Bold,
                    )
                },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = stringResource(R.string.action_back))
                    }
                },
                // Шапка экрана окрашена в цвет зоны
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = zoneColors.accent,
                    titleContentColor = zoneColors.onAccent,
                    navigationIconContentColor = zoneColors.onAccent,
                ),
            )
        },
        floatingActionButton = {
            FloatingActionButton(
                onClick = onAddTask,
                containerColor = MaterialTheme.colorScheme.primary,
                contentColor = MaterialTheme.colorScheme.onPrimary,
            ) {
                Icon(Icons.Filled.Add, contentDescription = stringResource(R.string.action_add_task))
            }
        },
        snackbarHost = { SnackbarHost(snackbarHostState) },
        containerColor = zoneColors.container,
    ) { innerPadding ->
        if (uiState.active.isEmpty() && uiState.done.isEmpty()) {
            Box(
                Modifier
                    .padding(innerPadding)
                    .fillMaxSize()
                    .padding(24.dp),
                contentAlignment = Alignment.Center,
            ) {
                Text(
                    text = stringResource(R.string.zone_empty_full),
                    textAlign = TextAlign.Center,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            return@Scaffold
        }

        LazyColumn(
            modifier = Modifier
                .padding(innerPadding)
                .fillMaxSize(),
            // Нижний отступ, чтобы последняя карточка не пряталась под кнопкой «+»
            contentPadding = PaddingValues(start = 12.dp, end = 12.dp, top = 12.dp, bottom = 88.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            item {
                Text(
                    text = stringResource(viewModel.zone.hintRes),
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            items(uiState.active, key = { it.id }) { task ->
                SwipeToDeleteBox(onDelete = { actions.onDelete(task) }) {
                    TaskCard(
                        task = task,
                        onClick = { onEditTask(task.id) },
                        onToggleDone = { done -> actions.onToggleDone(task, done) },
                    )
                }
            }
            if (uiState.done.isNotEmpty()) {
                item {
                    Text(
                        text = stringResource(R.string.zone_done_section, uiState.done.size),
                        style = MaterialTheme.typography.titleSmall,
                        modifier = Modifier.padding(top = 12.dp),
                    )
                }
                items(uiState.done, key = { it.id }) { task ->
                    SwipeToDeleteBox(onDelete = { actions.onDelete(task) }) {
                        TaskCard(
                            task = task,
                            onClick = { onEditTask(task.id) },
                            onToggleDone = { done -> actions.onToggleDone(task, done) },
                        )
                    }
                }
            }
        }
    }
}
