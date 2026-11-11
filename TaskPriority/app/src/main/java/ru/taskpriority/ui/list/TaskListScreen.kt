package ru.taskpriority.ui.list

import androidx.compose.foundation.horizontalScroll
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
import androidx.compose.foundation.rememberScrollState
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.ArrowDownward
import androidx.compose.material.icons.filled.ArrowUpward
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SegmentedButton
import androidx.compose.material3.SegmentedButtonDefaults
import androidx.compose.material3.SingleChoiceSegmentedButtonRow
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

/** Экран списка всех задач с фильтром и сортировкой. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TaskListScreen(
    onBack: () -> Unit,
    onAddTask: () -> Unit,
    onEditTask: (Long) -> Unit,
    viewModel: TaskListViewModel = viewModel(factory = AppViewModelProvider.Factory),
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    val snackbarHostState = remember { SnackbarHostState() }
    val actions = rememberTaskActionHandlers(viewModel, snackbarHostState)

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(stringResource(R.string.list_title), fontWeight = FontWeight.Bold) },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = stringResource(R.string.action_back))
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primary,
                    titleContentColor = MaterialTheme.colorScheme.onPrimary,
                    navigationIconContentColor = MaterialTheme.colorScheme.onPrimary,
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
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .padding(innerPadding)
                .fillMaxSize(),
        ) {
            // ---- Фильтр: Активные / Выполненные / Все ----
            SingleChoiceSegmentedButtonRow(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 12.dp, vertical = 8.dp),
            ) {
                TaskFilter.entries.forEachIndexed { index, filter ->
                    SegmentedButton(
                        selected = uiState.filter == filter,
                        onClick = { viewModel.onFilterSelected(filter) },
                        shape = SegmentedButtonDefaults.itemShape(index, TaskFilter.entries.size),
                    ) {
                        Text(stringResource(filter.labelRes), maxLines = 1)
                    }
                }
            }

            // ---- Сортировка: чипы + кнопка направления ----
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .horizontalScroll(rememberScrollState())
                    .padding(horizontal = 12.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                Text(stringResource(R.string.sort_label), style = MaterialTheme.typography.labelLarge)
                SortOption.entries.forEach { option ->
                    FilterChip(
                        selected = uiState.sort == option,
                        onClick = { viewModel.onSortSelected(option) },
                        label = { Text(stringResource(option.labelRes)) },
                    )
                }
                IconButton(onClick = viewModel::onToggleDirection) {
                    Icon(
                        imageVector = if (uiState.ascending) Icons.Filled.ArrowUpward else Icons.Filled.ArrowDownward,
                        contentDescription = stringResource(
                            if (uiState.ascending) R.string.sort_ascending else R.string.sort_descending
                        ),
                    )
                }
            }

            if (uiState.tasks.isEmpty()) {
                Box(
                    Modifier
                        .fillMaxSize()
                        .padding(24.dp),
                    contentAlignment = Alignment.Center,
                ) {
                    Text(
                        text = stringResource(R.string.list_empty),
                        textAlign = TextAlign.Center,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            } else {
                LazyColumn(
                    modifier = Modifier.fillMaxSize(),
                    contentPadding = PaddingValues(start = 12.dp, end = 12.dp, top = 8.dp, bottom = 88.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    items(uiState.tasks, key = { it.id }) { task ->
                        SwipeToDeleteBox(onDelete = { actions.onDelete(task) }) {
                            TaskCard(
                                task = task,
                                showZone = true,
                                onClick = { onEditTask(task.id) },
                                onToggleDone = { done -> actions.onToggleDone(task, done) },
                            )
                        }
                    }
                }
            }
        }
    }
}
