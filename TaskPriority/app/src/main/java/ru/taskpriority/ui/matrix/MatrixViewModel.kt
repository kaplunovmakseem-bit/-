package ru.taskpriority.ui.matrix

import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn
import ru.taskpriority.data.Task
import ru.taskpriority.data.TaskRepository
import ru.taskpriority.domain.PriorityZone
import ru.taskpriority.domain.zone
import ru.taskpriority.domain.zoneTaskOrder
import ru.taskpriority.ui.TaskActionsViewModel

/** Состояние главного экрана: активные задачи, разложенные по зонам. */
data class MatrixUiState(
    val tasksByZone: Map<PriorityZone, List<Task>> = PriorityZone.entries.associateWith { emptyList() },
)

class MatrixViewModel(repository: TaskRepository) : TaskActionsViewModel(repository) {

    /**
     * Берём поток всех задач из БД, оставляем невыполненные и группируем по зонам.
     * stateIn превращает Flow в StateFlow, который экран читает через collectAsStateWithLifecycle.
     */
    val uiState: StateFlow<MatrixUiState> = repository.tasks
        .map { tasks ->
            val active = tasks.filter { !it.isDone }
            MatrixUiState(
                tasksByZone = PriorityZone.entries.associateWith { zone ->
                    active.filter { it.zone == zone }.sortedWith(zoneTaskOrder)
                }
            )
        }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), MatrixUiState())
}
