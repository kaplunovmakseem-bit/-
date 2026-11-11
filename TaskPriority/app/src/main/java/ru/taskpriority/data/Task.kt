package ru.taskpriority.data

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * Задача — одна строка в таблице `tasks` базы данных Room.
 *
 * Даты храним числами, чтобы не писать конвертеры типов:
 *  - [dueDateEpochDay] — номер дня от 01.01.1970 (LocalDate.toEpochDay()), null — срока нет;
 *  - [createdAt] — момент создания в миллисекундах (System.currentTimeMillis()).
 */
@Entity(tableName = "tasks")
data class Task(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val title: String,
    val description: String = "",
    /** Значимость от 1 до 5. */
    val importance: Int,
    /** Сложность от 1 до 5. */
    val difficulty: Int,
    @ColumnInfo(name = "due_date")
    val dueDateEpochDay: Long? = null,
    @ColumnInfo(name = "is_done")
    val isDone: Boolean = false,
    @ColumnInfo(name = "created_at")
    val createdAt: Long = System.currentTimeMillis(),
)
