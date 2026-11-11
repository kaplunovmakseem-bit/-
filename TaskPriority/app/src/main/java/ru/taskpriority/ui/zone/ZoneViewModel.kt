package ru.taskpriority.ui.zone

import androidx.lifecycle.SavedStateHandle
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
import ru.taskpriority.ui.navigation.Routes

data class ZoneUiState(
    val active: List<Task> = emptyList(),
    val done: List<Task> = emptyList(),
)

/** ViewModel экрана одной зоны. Имя зоны приходит аргументом навигации. */
class ZoneViewModel(
    savedStateHandle: SavedStateHandle,
    repository: TaskRepository,
) : TaskActionsViewModel(repository) {

    val zone: PriorityZone = PriorityZone.valueOf(checkNotNull(savedStateHandle.get<String>(Routes.ARG_ZONE)))

    val uiState: StateFlow<ZoneUiState> = repository.tasks
        .map { tasks ->
            val inZone = tasks.filter { it.zone == zone }.sortedWith(zoneTaskOrder)
            ZoneUiState(
                active = inZone.filter { !it.isDone },
                done = inZone.filter { it.isDone },
            )
        }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), ZoneUiState())
}
