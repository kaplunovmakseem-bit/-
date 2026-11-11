package ru.taskpriority.ui.list

import androidx.annotation.StringRes
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.update
import ru.taskpriority.R
import ru.taskpriority.data.Task
import ru.taskpriority.data.TaskRepository
import ru.taskpriority.ui.TaskActionsViewModel

/** Варианты сортировки. [defaultAscending] — направление, выбираемое при переключении на этот вариант. */
enum class SortOption(@StringRes val labelRes: Int, val defaultAscending: Boolean) {
    IMPORTANCE(R.string.sort_importance, defaultAscending = false), // сначала самые значимые
    DIFFICULTY(R.string.sort_difficulty, defaultAscending = true),  // сначала самые лёгкие
    DUE_DATE(R.string.sort_due_date, defaultAscending = true),      // сначала ближайшие сроки
}

enum class TaskFilter(@StringRes val labelRes: Int) {
    ACTIVE(R.string.filter_active),
    DONE(R.string.filter_done),
    ALL(R.string.filter_all),
}

data class TaskListUiState(
    val tasks: List<Task> = emptyList(),
    val sort: SortOption = SortOption.IMPORTANCE,
    val ascending: Boolean = SortOption.IMPORTANCE.defaultAscending,
    val filter: TaskFilter = TaskFilter.ACTIVE,
)

/** Настройки, которые выбирает пользователь (сортировка и фильтр). */
private data class ListSettings(
    val sort: SortOption = SortOption.IMPORTANCE,
    val ascending: Boolean = SortOption.IMPORTANCE.defaultAscending,
    val filter: TaskFilter = TaskFilter.ACTIVE,
)

class TaskListViewModel(repository: TaskRepository) : TaskActionsViewModel(repository) {

    private val settings = MutableStateFlow(ListSettings())

    /**
     * combine пересчитывает список каждый раз, когда меняются задачи в БД
     * ИЛИ пользователь меняет сортировку/фильтр.
     */
    val uiState: StateFlow<TaskListUiState> = combine(repository.tasks, settings) { tasks, s ->
        TaskListUiState(
            tasks = tasks.filterBy(s.filter).sortBy(s.sort, s.ascending),
            sort = s.sort,
            ascending = s.ascending,
            filter = s.filter,
        )
    }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), TaskListUiState())

    fun onSortSelected(option: SortOption) {
        settings.update { current ->
            if (current.sort == option) current // повторное нажатие ничего не меняет
            else current.copy(sort = option, ascending = option.defaultAscending)
        }
    }

    fun onToggleDirection() {
        settings.update { it.copy(ascending = !it.ascending) }
    }

    fun onFilterSelected(filter: TaskFilter) {
        settings.update { it.copy(filter = filter) }
    }
}

private fun List<Task>.filterBy(taskFilter: TaskFilter): List<Task> = when (taskFilter) {
    TaskFilter.ACTIVE -> filter { !it.isDone }
    TaskFilter.DONE -> filter { it.isDone }
    TaskFilter.ALL -> this
}

/**
 * Сортировка устойчивая: задачи с одинаковым значением остаются в исходном порядке
 * (из БД они приходят от новых к старым).
 * Задачи без срока при сортировке по сроку всегда оказываются в конце.
 */
private fun List<Task>.sortBy(option: SortOption, ascending: Boolean): List<Task> = when (option) {
    SortOption.IMPORTANCE -> if (ascending) sortedBy { it.importance } else sortedByDescending { it.importance }
    SortOption.DIFFICULTY -> if (ascending) sortedBy { it.difficulty } else sortedByDescending { it.difficulty }
    SortOption.DUE_DATE -> {
        val order: Comparator<Long> = if (ascending) naturalOrder() else reverseOrder()
        sortedWith(compareBy<Task, Long?>(nullsLast(order)) { it.dueDateEpochDay })
    }
}
