package ru.taskpriority

import android.app.Application
import ru.taskpriority.data.TaskDatabase
import ru.taskpriority.data.TaskRepository

/**
 * Класс приложения — живёт всё время работы приложения.
 * Здесь создаём базу данных и репозиторий в одном экземпляре (простая ручная DI без Hilt).
 */
class TaskPriorityApp : Application() {

    val repository: TaskRepository by lazy {
        TaskRepository(TaskDatabase.create(this).taskDao())
    }
}
