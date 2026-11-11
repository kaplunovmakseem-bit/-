package ru.taskpriority.data

import kotlinx.coroutines.flow.Flow

/**
 * Репозиторий — единая точка доступа к данным для ViewModel.
 * Сейчас он просто проксирует DAO, но сюда удобно добавлять, например, синхронизацию с сервером.
 */
class TaskRepository(private val dao: TaskDao) {

    val tasks: Flow<List<Task>> = dao.observeAll()

    suspend fun getTask(id: Long): Task? = dao.getById(id)

    suspend fun save(task: Task) {
        dao.upsert(task)
    }

    suspend fun delete(task: Task) = dao.delete(task)

    /** Повторно вставляет удалённую задачу с тем же id — используется для «Отменить» в Snackbar. */
    suspend fun restore(task: Task) {
        dao.upsert(task)
    }

    suspend fun setDone(task: Task, done: Boolean) {
        dao.upsert(task.copy(isDone = done))
    }
}
