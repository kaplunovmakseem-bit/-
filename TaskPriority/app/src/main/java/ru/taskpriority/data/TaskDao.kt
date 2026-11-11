package ru.taskpriority.data

import androidx.room.Dao
import androidx.room.Delete
import androidx.room.Query
import androidx.room.Upsert
import kotlinx.coroutines.flow.Flow

/**
 * DAO — набор запросов к таблице задач. Реализацию генерирует Room (через KSP).
 * Методы, возвращающие Flow, автоматически присылают новый список при любом изменении таблицы —
 * поэтому экраны обновляются сами.
 */
@Dao
interface TaskDao {

    @Query("SELECT * FROM tasks ORDER BY created_at DESC")
    fun observeAll(): Flow<List<Task>>

    @Query("SELECT * FROM tasks WHERE id = :id")
    suspend fun getById(id: Long): Task?

    /** Вставка новой задачи или обновление существующей (по id). */
    @Upsert
    suspend fun upsert(task: Task): Long

    @Delete
    suspend fun delete(task: Task)
}
