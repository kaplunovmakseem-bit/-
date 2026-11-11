package ru.taskpriority.ui.edit

import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import ru.taskpriority.data.Task
import ru.taskpriority.data.TaskRepository
import ru.taskpriority.domain.PriorityZone
import ru.taskpriority.ui.navigation.Routes

/** Всё, что отображает экран редактирования. */
data class EditTaskUiState(
    val isNew: Boolean = true,
    val isLoading: Boolean = false,
    val title: String = "",
    val description: String = "",
    val importance: Int = 3,
    val difficulty: Int = 2,
    val dueDateEpochDay: Long? = null,
    val isDone: Boolean = false,
    val createdAt: Long = System.currentTimeMillis(),
    /** true — показать ошибку «Введите название». */
    val showTitleError: Boolean = false,
    /** true — задача сохранена, экран можно закрывать. */
    val isSaved: Boolean = false,
) {
    /** Зона пересчитывается на лету, пока пользователь двигает слайдеры. */
    val zone: PriorityZone get() = PriorityZone.of(importance, difficulty)
}

class EditTaskViewModel(
    savedStateHandle: SavedStateHandle,
    private val repository: TaskRepository,
) : ViewModel() {

    /** id редактируемой задачи или [Routes.NEW_TASK_ID] для новой. */
    private val taskId: Long = savedStateHandle.get<Long>(Routes.ARG_TASK_ID) ?: Routes.NEW_TASK_ID

    private val _uiState = MutableStateFlow(
        EditTaskUiState(isNew = taskId == Routes.NEW_TASK_ID, isLoading = taskId != Routes.NEW_TASK_ID)
    )
    val uiState: StateFlow<EditTaskUiState> = _uiState.asStateFlow()

    init {
        // Для существующей задачи загружаем её из БД и заполняем поля.
        if (taskId != Routes.NEW_TASK_ID) {
            viewModelScope.launch {
                val task = repository.getTask(taskId)
                _uiState.update { state ->
                    if (task == null) state.copy(isLoading = false, isNew = true)
                    else state.copy(
                        isLoading = false,
                        title = task.title,
                        description = task.description,
                        importance = task.importance,
                        difficulty = task.difficulty,
                        dueDateEpochDay = task.dueDateEpochDay,
                        isDone = task.isDone,
                        createdAt = task.createdAt,
                    )
                }
            }
        }
    }

    fun onTitleChange(value: String) = _uiState.update { it.copy(title = value, showTitleError = false) }
    fun onDescriptionChange(value: String) = _uiState.update { it.copy(description = value) }
    fun onImportanceChange(value: Int) = _uiState.update { it.copy(importance = value) }
    fun onDifficultyChange(value: Int) = _uiState.update { it.copy(difficulty = value) }
    fun onDueDateChange(epochDay: Long?) = _uiState.update { it.copy(dueDateEpochDay = epochDay) }
    fun onDoneChange(value: Boolean) = _uiState.update { it.copy(isDone = value) }

    fun save() {
        val state = _uiState.value
        // Название обязательно — без него не сохраняем.
        if (state.title.isBlank()) {
            _uiState.update { it.copy(showTitleError = true) }
            return
        }
        viewModelScope.launch {
            repository.save(
                Task(
                    // id = 0 означает «новая задача» — Room сам выдаст id.
                    id = if (state.isNew) 0 else taskId,
                    title = state.title.trim(),
                    description = state.description.trim(),
                    importance = state.importance,
                    difficulty = state.difficulty,
                    dueDateEpochDay = state.dueDateEpochDay,
                    isDone = state.isDone,
                    createdAt = state.createdAt,
                )
            )
            _uiState.update { it.copy(isSaved = true) }
        }
    }
}
