package ru.taskpriority.ui

import androidx.lifecycle.ViewModelProvider.AndroidViewModelFactory.Companion.APPLICATION_KEY
import androidx.lifecycle.createSavedStateHandle
import androidx.lifecycle.viewmodel.CreationExtras
import androidx.lifecycle.viewmodel.initializer
import androidx.lifecycle.viewmodel.viewModelFactory
import ru.taskpriority.TaskPriorityApp
import ru.taskpriority.ui.edit.EditTaskViewModel
import ru.taskpriority.ui.list.TaskListViewModel
import ru.taskpriority.ui.matrix.MatrixViewModel
import ru.taskpriority.ui.zone.ZoneViewModel

/**
 * Фабрика всех ViewModel приложения.
 * Передаёт им репозиторий из [TaskPriorityApp] и SavedStateHandle
 * (в нём лежат аргументы навигации: id задачи, имя зоны).
 */
object AppViewModelProvider {
    val Factory = viewModelFactory {
        initializer { MatrixViewModel(app().repository) }
        initializer { ZoneViewModel(createSavedStateHandle(), app().repository) }
        initializer { TaskListViewModel(app().repository) }
        initializer { EditTaskViewModel(createSavedStateHandle(), app().repository) }
    }
}

private fun CreationExtras.app(): TaskPriorityApp = this[APPLICATION_KEY] as TaskPriorityApp
