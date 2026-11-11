package ru.taskpriority.domain

import ru.taskpriority.data.Task

/**
 * Порядок задач внутри зоны: сначала с ближайшим сроком (без срока — в конце),
 * затем более значимые, затем более лёгкие.
 */
val zoneTaskOrder: Comparator<Task> =
    compareBy<Task, Long?>(nullsLast(naturalOrder())) { it.dueDateEpochDay }
        .thenByDescending { it.importance }
        .thenBy { it.difficulty }
