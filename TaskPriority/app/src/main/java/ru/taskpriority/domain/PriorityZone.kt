package ru.taskpriority.domain

import androidx.annotation.StringRes
import ru.taskpriority.R
import ru.taskpriority.data.Task

/**
 * ПОРОГИ РАСПРЕДЕЛЕНИЯ — единственное место, где они заданы.
 *
 * Значимость считается «высокой», если она >= [HIGH_IMPORTANCE_FROM].
 * Сложность считается «высокой», если она >= [HIGH_DIFFICULTY_FROM].
 *
 * Например, если поменять HIGH_IMPORTANCE_FROM на 4, то задачи со значимостью 3
 * станут «низкозначимыми» и переедут в зоны «Между делом» / «Отложить».
 */
object ZoneThresholds {
    const val HIGH_IMPORTANCE_FROM = 3
    const val HIGH_DIFFICULTY_FROM = 3

    /** Минимальное и максимальное значение шкал значимости и сложности. */
    const val SCALE_MIN = 1
    const val SCALE_MAX = 5
}

/**
 * Четыре зоны матрицы. Порядок объявления = порядок ячеек в матрице 2×2:
 *
 *   | Сделать сейчас | Запланировать |
 *   | Между делом    | Отложить      |
 */
enum class PriorityZone(
    @StringRes val titleRes: Int,
    @StringRes val hintRes: Int,
) {
    DO_NOW(R.string.zone_do_now, R.string.zone_do_now_hint),
    PLAN(R.string.zone_plan, R.string.zone_plan_hint),
    IN_BETWEEN(R.string.zone_in_between, R.string.zone_in_between_hint),
    POSTPONE(R.string.zone_postpone, R.string.zone_postpone_hint);

    companion object {
        /** Главное правило распределения: по значимости и сложности выбираем зону. */
        fun of(importance: Int, difficulty: Int): PriorityZone {
            val important = importance >= ZoneThresholds.HIGH_IMPORTANCE_FROM
            val hard = difficulty >= ZoneThresholds.HIGH_DIFFICULTY_FROM
            return when {
                important && !hard -> DO_NOW
                important && hard -> PLAN
                !important && !hard -> IN_BETWEEN
                else -> POSTPONE
            }
        }
    }
}

/** Удобное расширение: зона конкретной задачи. */
val Task.zone: PriorityZone
    get() = PriorityZone.of(importance, difficulty)
