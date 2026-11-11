package ru.taskpriority.ui.matrix

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.List
import androidx.compose.material.icons.filled.Add
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
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
import ru.taskpriority.data.Task
import ru.taskpriority.domain.PriorityZone
import ru.taskpriority.ui.AppViewModelProvider
import ru.taskpriority.ui.components.SwipeToDeleteBox
import ru.taskpriority.ui.components.TaskActionHandlers
import ru.taskpriority.ui.components.TaskCard
import ru.taskpriority.ui.components.ZoneHeader
import ru.taskpriority.ui.components.rememberTaskActionHandlers
import ru.taskpriority.ui.theme.colors

/**
 * Главный экран — матрица 2×2.
 * Верхний ряд — значимые задачи, нижний — менее значимые;
 * левый столбец — лёгкие, правый — сложные.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MatrixScreen(
    onOpenZone: (PriorityZone) -> Unit,
    onOpenList: () -> Unit,
    onAddTask: () -> Unit,
    onEditTask: (Long) -> Unit,
    viewModel: MatrixViewModel = viewModel(factory = AppViewModelProvider.Factory),
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    val snackbarHostState = remember { SnackbarHostState() }
    val actions = rememberTaskActionHandlers(viewModel, snackbarHostState)

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(stringResource(R.string.matrix_title), fontWeight = FontWeight.Bold) },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primary,
                    titleContentColor = MaterialTheme.colorScheme.onPrimary,
                    actionIconContentColor = MaterialTheme.colorScheme.onPrimary,
                ),
                actions = {
                    IconButton(onClick = onOpenList) {
                        Icon(Icons.AutoMirrored.Filled.List, contentDescription = stringResource(R.string.list_title))
                    }
                },
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
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .padding(innerPadding)
                .fillMaxSize()
                .padding(8.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            // PriorityZone.entries идут в порядке: DO_NOW, PLAN, IN_BETWEEN, POSTPONE —
            // разбиваем их по два, получаем два ряда матрицы.
            PriorityZone.entries.chunked(2).forEach { rowZones ->
                Row(
                    modifier = Modifier.weight(1f),
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    rowZones.forEach { zone ->
                        ZoneCell(
                            zone = zone,
                            tasks = uiState.tasksByZone[zone].orEmpty(),
                            actions = actions,
                            onOpenZone = { onOpenZone(zone) },
                            onEditTask = onEditTask,
                            modifier = Modifier
                                .weight(1f)
                                .fillMaxSize(),
                        )
                    }
                }
            }
        }
    }
}

/** Одна ячейка матрицы: цветная шапка + прокручиваемый список компактных карточек. */
@Composable
private fun ZoneCell(
    zone: PriorityZone,
    tasks: List<Task>,
    actions: TaskActionHandlers,
    onOpenZone: () -> Unit,
    onEditTask: (Long) -> Unit,
    modifier: Modifier = Modifier,
) {
    val colors = zone.colors()
    // Нажатие на любое свободное место ячейки (в том числе на шапку) открывает зону целиком.
    Card(
        onClick = onOpenZone,
        modifier = modifier,
        colors = CardDefaults.cardColors(containerColor = colors.container),
    ) {
        ZoneHeader(zone = zone, count = tasks.size)
        if (tasks.isEmpty()) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(12.dp),
                contentAlignment = Alignment.Center,
            ) {
                Text(
                    text = stringResource(R.string.zone_empty),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    textAlign = TextAlign.Center,
                )
            }
        } else {
            LazyColumn(
                modifier = Modifier.fillMaxWidth(),
                contentPadding = PaddingValues(6.dp),
                verticalArrangement = Arrangement.spacedBy(6.dp),
            ) {
                items(tasks, key = { it.id }) { task ->
                    SwipeToDeleteBox(onDelete = { actions.onDelete(task) }) {
                        TaskCard(
                            task = task,
                            compact = true,
                            onClick = { onEditTask(task.id) },
                            onToggleDone = { done -> actions.onToggleDone(task, done) },
                        )
                    }
                }
            }
        }
    }
}
