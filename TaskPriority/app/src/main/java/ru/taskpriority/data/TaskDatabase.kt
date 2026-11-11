package ru.taskpriority.data

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase

/**
 * База данных приложения. Если в будущем поменяете поля [Task],
 * увеличьте version и добавьте миграцию (или fallbackToDestructiveMigration для разработки).
 */
@Database(entities = [Task::class], version = 1, exportSchema = false)
abstract class TaskDatabase : RoomDatabase() {

    abstract fun taskDao(): TaskDao

    companion object {
        fun create(context: Context): TaskDatabase =
            Room.databaseBuilder(context, TaskDatabase::class.java, "tasks.db").build()
    }
}
