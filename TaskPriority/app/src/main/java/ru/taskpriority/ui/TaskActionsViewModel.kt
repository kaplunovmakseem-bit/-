package ru.taskpriority.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.launch
import ru.taskpriority.data.Task
import ru.taskpriority.data.TaskRepository

/**
 * Общие действия с задачей, которые есть на нескольких экранах:
 * отметить выполненной, удалить и восстановить (отмена удаления).
 * Экранные ViewModel наследуются от этого класса, чтобы не дублировать код.
 */
abstract class TaskActionsViewModel(
    protected val repository: TaskRepository,
) : ViewModel() {

    fun setDone(task: Task, done: Boolean) {
        viewModelScope.launch { repository.setDone(task, done) }
    }

    fun delete(task: Task) {
        viewModelScope.launch { repository.delete(task) }
    }

    fun restore(task: Task) {
        viewModelScope.launch { repository.restore(task) }
    }
}
