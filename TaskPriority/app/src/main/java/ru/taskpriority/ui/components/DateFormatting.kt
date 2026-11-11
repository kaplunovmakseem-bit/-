package ru.taskpriority.ui.components

import java.time.LocalDate
import java.time.format.DateTimeFormatter
import java.util.Locale

/** Миллисекунд в сутках — нужно для перевода значения DatePicker в номер дня. */
const val MILLIS_PER_DAY = 24L * 60 * 60 * 1000

private val dueDateFormatter = DateTimeFormatter.ofPattern("d MMM yyyy", Locale.forLanguageTag("ru"))

/** Номер дня (epochDay) → строка вида «5 мар. 2026». */
fun formatEpochDay(epochDay: Long): String = LocalDate.ofEpochDay(epochDay).format(dueDateFormatter)

fun todayEpochDay(): Long = LocalDate.now().toEpochDay()

/** Просрочена ли задача: срок есть, он раньше сегодняшнего дня и задача не выполнена. */
fun isOverdue(dueEpochDay: Long?, isDone: Boolean): Boolean =
    dueEpochDay != null && !isDone && dueEpochDay < todayEpochDay()
